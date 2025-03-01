import logging
import uuid
import time
import openai

from django.shortcuts import get_object_or_404
from concurrent.futures import Future
from rest_framework import viewsets
from rest_framework.response import Response as DRFResponse
from rq.job import Job

from .models import DataSource
from .models import DataSourceEntry
from .models import DataSourceEntryStatus
from .models import DataSourceType
from .models import DataSourceLabels
from .serializers import DataSourceEntrySerializer
from .serializers import DataSourceSerializer
from .serializers import DataSourceTypeSerializer
from .serializers import DataSourceLabelsSerializer
from llmstack.apps.tasks import add_data_entry_task, extract_urls_task, resync_data_entry_task, delete_data_entry_task, \
    delete_data_source_task, add_labels_data_task, update_labels_data_task
from llmstack.datasources.handlers.datasource_processor import DataSourceProcessor
from llmstack.datasources.types import DataSourceTypeFactory
from llmstack.jobs.adhoc import DataSourceEntryProcessingJob, ExtractURLJob, DataSourceLabelsProcessingJob

logger = logging.getLogger(__name__)


class DataSourceTypeViewSet(viewsets.ModelViewSet):
    queryset = DataSourceType.objects.all()
    serializer_class = DataSourceTypeSerializer

    def get(self, request):
        return DRFResponse(DataSourceTypeSerializer(instance=self.queryset, many=True).data)


class DataSourceEntryViewSet(viewsets.ModelViewSet):
    queryset = DataSourceEntry.objects.all()
    serializer_class = DataSourceEntrySerializer

    def get(self, request, uid=None):
        if uid:
            datasource_entry_object = get_object_or_404(
                DataSourceEntry, uuid=uuid.UUID(uid),
            )
            if not datasource_entry_object.user_can_read(request.user):
                return DRFResponse(status=404)

            return DRFResponse(DataSourceEntrySerializer(instance=datasource_entry_object).data)
        datasources = DataSource.objects.filter(owner=request.user)
        datasource_entries = DataSourceEntry.objects.filter(
            datasource__in=datasources,
        )
        return DRFResponse(DataSourceEntrySerializer(instance=datasource_entries, many=True).data)

    def multiGet(self, request, uids):
        datasource_entries = DataSourceEntry.objects.filter(uuid__in=uids)
        return DRFResponse(DataSourceEntrySerializer(instance=datasource_entries, many=True).data)

    def delete(self, request, uid):
        datasource_entry_object = get_object_or_404(
            DataSourceEntry, uuid=uuid.UUID(uid),
        )
        if datasource_entry_object.datasource.owner != request.user:
            return DRFResponse(status=404)

        delete_data_entry_task(
            datasource_entry_object.datasource, datasource_entry_object,
        )

        return DRFResponse(status=202)

    def text_content(self, request, uid):
        datasource_entry_object = get_object_or_404(
            DataSourceEntry, uuid=uuid.UUID(uid),
        )
        if not datasource_entry_object.user_can_read(request.user):
            return DRFResponse(status=404)

        datasource_type = datasource_entry_object.datasource.type
        datasource_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource_type,
        )
        datasource_handler = datasource_handler_cls(
            datasource_entry_object.datasource,
        )
        metadata, content = datasource_handler.get_entry_text(
            datasource_entry_object.config,
        )
        return DRFResponse({'content': content, 'metadata': metadata})

    def resync(self, request, uid):
        datasource_entry_object = get_object_or_404(
            DataSourceEntry, uuid=uuid.UUID(uid),
        )
        if datasource_entry_object.datasource.owner != request.user:
            return DRFResponse(status=404)

        resync_data_entry_task(
            datasource_entry_object.datasource, datasource_entry_object,
        )

        return DRFResponse(status=202)


class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer

    def get(self, request, uid=None):
        if uid:
            # TODO: return data source entries along with the data source
            return DRFResponse(DataSourceSerializer(
                instance=get_object_or_404(DataSource, uuid=uuid.UUID(uid), owner=request.user)).data)
        return DRFResponse(
            DataSourceSerializer(instance=self.queryset.filter(owner=request.user).order_by('-updated_at'),
                                 many=True).data)

    def getEntries(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )
        datasource_entries = DataSourceEntry.objects.filter(
            datasource=datasource,
        )
        return DRFResponse(DataSourceEntrySerializer(instance=datasource_entries, many=True).data)

    def post(self, request):
        owner = request.user
        datasource_type = get_object_or_404(
            DataSourceType, id=request.data['type'],
        )

        datasource = DataSource(
            name=request.data['name'],
            owner=owner,
            type=datasource_type,
        )
        # If this is an external data source, then we need to save the config in datasource object
        if datasource_type.is_external_datasource:
            datasource_type_cls = DataSourceTypeFactory.get_datasource_type_handler(
                datasource.type)
            if not datasource_type_cls:
                logger.error(
                    'No handler found for data source type {datasource.type}',
                )
                return DRFResponse({'errors': ['No handler found for data source type']}, status=400)

            datasource_handler: DataSourceProcessor = datasource_type_cls(
                datasource)
            if not datasource_handler:
                logger.error(
                    f'Error while creating handler for data source {datasource.name}')
                return DRFResponse({'errors': ['Error while creating handler for data source type']}, status=400)
            config = datasource_type_cls.process_validate_config(
                request.data['config'], datasource)
            datasource.config = config

        datasource.save()
        return DRFResponse(DataSourceSerializer(instance=datasource).data, status=201)

    def delete(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )

        # Delete all datasource entries associated with the datasource
        datasource_entries = DataSourceEntry.objects.filter(
            datasource=datasource,
        )
        for entry in datasource_entries:
            DataSourceEntryViewSet().delete(request=request, uid=str(entry.uuid))

        # Delete the data from data store
        delete_data_source_task(datasource)

        datasource.delete()
        return DRFResponse(status=204)

    def add_entry(self, request, uid):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(uid), owner=request.user,
        )
        if datasource and datasource.type.is_external_datasource:
            return DRFResponse({'errors': ['Cannot add entry to external data source']}, status=400)

        entry_data = request.data['entry_data']
        entry_metadata = dict(map(lambda x: (f'md_{x}', request.data['entry_metadata'][x]),
                                  request.data['entry_metadata'].keys())) if 'entry_metadata' in request.data else {
        }
        if not entry_data:
            return DRFResponse({'errors': ['No entry_data provided']}, status=400)

        datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource.type,
        )
        if not datasource_entry_handler_cls:
            logger.error(
                'No handler found for data source type {datasource.type}',
            )
            return DRFResponse({'errors': ['No handler found for data source type']}, status=400)

        datasource_entry_handler: DataSourceProcessor = datasource_entry_handler_cls(
            datasource,
        )

        if not datasource_entry_handler:
            logger.error(
                'Error while creating handler for data source type {datasource.type}',
            )
            return DRFResponse({'errors': ['Error while creating handler for data source type']}, status=400)

        # Validate the entry data against the data source type and add the entry
        datasource_entry_items = datasource_entry_handler.validate_and_process(
            entry_data,
        )

        processed_datasource_entry_items = []
        for datasource_entry_item in datasource_entry_items:
            datasource_entry_object = DataSourceEntry.objects.create(
                datasource=datasource,
                name=datasource_entry_item.name,
                status=DataSourceEntryStatus.PROCESSING,
            )
            datasource_entry_object.save()
            processed_datasource_entry_items.append(
                datasource_entry_item.copy(update={'uuid': str(
                    datasource_entry_object.uuid), 'metadata': entry_metadata}),
            )

        # Trigger a task to process the data source entry
        try:
            job = DataSourceEntryProcessingJob.create(
                func=add_data_entry_task, args=[
                    datasource, processed_datasource_entry_items,
                ],
            ).add_to_queue()
            return DRFResponse({'success': True}, status=202)
        except Exception as e:
            logger.error(f'Error while adding entry to data source: {e}')
            return DRFResponse({'errors': [str(e)]}, status=500)

    def extract_urls(self, request):
        if not request.user.is_authenticated or request.method != 'POST':
            return DRFResponse(status=403)

        url = request.data.get('url', None)
        if not url:
            return DRFResponse({'urls': []})

        if not url.startswith('https://') and not url.startswith('http://'):
            url = f'https://{url}'

        logger.info("Staring job to extract urls")

        job = ExtractURLJob.create(
            func=extract_urls_task, args=[
                url
            ],
        ).add_to_queue()

        # Wait for job to finish and return the result
        while True:
            time.sleep(1)

            if isinstance(job, Future) and job.done():
                break
            elif isinstance(job, Job) and (job.is_failed or job.is_finished or job.is_stopped or job.is_canceled):
                break

        if isinstance(job, Future):
            urls = job.result()
        elif job.is_failed or job.is_stopped or job.is_canceled:
            urls = [url]
        else:
            urls = job.result

        return DRFResponse({'urls': urls})


class DataSourceLabelsViewSet(viewsets.ModelViewSet):
    queryset = DataSourceLabels.objects.all()
    serializer_class = DataSourceLabelsSerializer

    def get(self, request, uid=None):
        if uid:
            return DRFResponse(
                DataSourceLabelsSerializer(instance=get_object_or_404(DataSourceLabels, uuid=uuid.UUID(uid))).data)
        return DRFResponse(DataSourceLabelsSerializer(instance=self.queryset.order_by('-updated_at'), many=True).data)

    def post(self, request):
        datasource = get_object_or_404(
            DataSource, uuid=uuid.UUID(request.data['data_source']),
        )

        print(request.data)
        print(request.user)
        datasource_entry_object = DataSourceEntry.objects.filter(
            datasource=datasource,
        )[0]
        datasource_type = datasource_entry_object.datasource.type
        datasource_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource_type,
        )
        datasource_handler = datasource_handler_cls(
            datasource_entry_object.datasource,
        )
        _, content = datasource_handler.get_entry_text(
            datasource_entry_object.config,
        )
        labels = request.data["labels"]
        text = "\n".join([content[label["start"]: label["end"]] for label in labels if label["tag"] == "GUIDE"])

        datasource_labels = DataSourceLabels(
            data_source=datasource,
            data_source_name=datasource.name,
            labels=request.data['labels'],
            owner_id=request.data['user_id'],
            labels_name=request.data['name'],
        )
        datasource_labels.save()
        try:
            job = DataSourceLabelsProcessingJob.create(
                func=add_labels_data_task, args=[
                    datasource, text, request.data["name"], str(datasource_labels.uuid)
                ],
            ).add_to_queue()
            return DRFResponse(DataSourceLabelsSerializer(instance=datasource_labels).data, status=201)
        except Exception as e:
            logger.error(f'Error while adding entry to data source: {e}')
            return DRFResponse({'errors': [str(e)]}, status=500)

    def put(self, request, uid):
        datasource_labels = get_object_or_404(
            DataSourceLabels, uuid=uuid.UUID(uid),
        )
        datasource_entry_object = DataSourceEntry.objects.filter(
            datasource=datasource_labels.data_source,
        )[0]
        datasource_type = datasource_entry_object.datasource.type
        datasource_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource_type,
        )
        datasource_handler = datasource_handler_cls(
            datasource_entry_object.datasource,
        )
        _, content = datasource_handler.get_entry_text(
            datasource_entry_object.config,
        )
        labels = request.data["labels"]
        text = "\n".join([content[label["start"]: label["end"]] for label in labels if label["tag"] == "GUIDE"])
        datasource_labels.labels = labels
        old_name = datasource_labels.labels_name
        name = request.data['name']
        datasource_labels.labels_name = name
        variables = request.data['variables']
        if variables:
            datasource_labels.variables = variables
        metadata = {"data": text}
        for variable in variables:
            print(variable)
            metadata[variable["key"]] = [variable["value"], variable["description"]]
        datasource_labels.save()

        try:
            job = DataSourceLabelsProcessingJob.create(
                func=update_labels_data_task, args=[
                    datasource_labels.data_source, metadata, name, uid, old_name
                ],
            ).add_to_queue()
            return DRFResponse(DataSourceLabelsSerializer(instance=datasource_labels).data, status=200)
        except Exception as e:
            logger.error(f'Error while adding entry to data source: {e}')
            return DRFResponse({'errors': [str(e)]}, status=500)

    def delete(self, request, uid):
        datasource_labels = get_object_or_404(
            DataSourceLabels, uuid=uuid.UUID(uid),
        )
        datasource_labels.delete()
        return DRFResponse(status=204)

    def getTextContent(self, request, uid):
        datasource_labels = get_object_or_404(
            DataSourceLabels, uuid=uuid.UUID(uid),
        )
        datasource_entry_object = DataSourceEntry.objects.filter(
            datasource=datasource_labels.data_source,
        )[0]
        datasource_type = datasource_entry_object.datasource.type
        datasource_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource_type,
        )
        datasource_handler = datasource_handler_cls(
            datasource_entry_object.datasource,
        )
        metadata, content = datasource_handler.get_entry_text(
            datasource_entry_object.config,
        )
        return DRFResponse({'content': content, 'metadata': metadata})

        # return DRFResponse(DataSourceEntrySerializer(instance=datasource_entries, many=False).data)

    def add_entry(self, request, uid):
        datasource_labels = get_object_or_404(
            DataSourceLabels, uuid=uuid.UUID(uid),
        )
        datasource = datasource_labels.data_source
        if datasource and datasource.type.is_external_datasource:
            return DRFResponse({'errors': ['Cannot add entry to external data source']}, status=400)

        entry_data = request.data['entry_data']
        entry_metadata = dict(map(lambda x: (f'md_{x}', request.data['entry_metadata'][x]),
                                  request.data['entry_metadata'].keys())) if 'entry_metadata' in request.data else {
        }
        if not entry_data:
            return DRFResponse({'errors': ['No entry_data provided']}, status=400)

        datasource_entry_handler_cls = DataSourceTypeFactory.get_datasource_type_handler(
            datasource.type,
        )
        if not datasource_entry_handler_cls:
            logger.error(
                'No handler found for data source type {datasource.type}',
            )
            return DRFResponse({'errors': ['No handler found for data source type']}, status=400)

        datasource_entry_handler: DataSourceProcessor = datasource_entry_handler_cls(
            datasource,
        )

        if not datasource_entry_handler:
            logger.error(
                'Error while creating handler for data source type {datasource.type}',
            )
            return DRFResponse({'errors': ['Error while creating handler for data source type']}, status=400)

        # Validate the entry data against the data source type and add the entry
        datasource_entry_items = datasource_entry_handler.validate_and_process(
            entry_data,
        )

        processed_datasource_entry_items = []
        for datasource_entry_item in datasource_entry_items:
            datasource_entry_object = DataSourceEntry.objects.create(
                datasource=datasource,
                name=datasource_entry_item.name,
                status=DataSourceEntryStatus.PROCESSING,
            )
            datasource_entry_object.save()
            processed_datasource_entry_items.append(
                datasource_entry_item.copy(update={'uuid': str(
                    datasource_entry_object.uuid), 'metadata': entry_metadata}),
            )

        # Trigger a task to process the data source entry
        try:
            job = DataSourceEntryProcessingJob.create(
                func=add_data_entry_task, args=[
                    datasource, processed_datasource_entry_items,
                ],
            ).add_to_queue()
            return DRFResponse({'success': True}, status=202)
        except Exception as e:
            logger.error(f'Error while adding entry to data source: {e}')
            return DRFResponse({'errors': [str(e)]}, status=500)
