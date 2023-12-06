import logging
import uuid
import pinecone
from typing import Any, Tuple
from typing import List
from uuid import uuid4

from pydantic import BaseModel
from django.conf import settings

from llmstack.common.blocks.data.store.vectorstore import Document, DocumentQuery, VectorStoreInterface


class PineconeConfiguration(BaseModel):
    pass


class Pinecone(VectorStoreInterface):
    """
    Pinecone vectorstore implementation
    """

    def __init__(self, pinecone_api_key="8f7fd7b3-ed9a-4d2f-8de5-4480a2539acb", pinecone_environment="gcp-starter"):
        super().__init__()
        pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)
        self._client = pinecone

    def add_text(self, index_name: str, document: Document, id_=None, **kwargs: Any):
        index = pinecone.Index(index_name)
        content_key = document.page_content_key
        content = document.page_content
        metadata = document.metadata
        metadata[content_key] = content
        try:
            index.upsert(
                vectors=[
                    (
                        id_ if id_ else str(uuid4()),
                        document.embeddings,
                        metadata
                    )
                ]
            )
        except Exception as e:
            print(e)

        return id_

    def add_texts(self, index_name: str, documents: List[Document], ids=None, **kwargs: Any):
        if ids is None:
            ids = None
        for document in documents:
            ids.append(self.add_text(index_name, document, kwargs=kwargs))
        return ids

    def update_document(self, index_name: str, id_: str, metadata=None, embeddings=None):
        kwargs = {"id": id_}
        index = pinecone.Index(index_name)
        if metadata is not None:
            kwargs["set_metadata"] = metadata
        if embeddings is not None:
            kwargs["values"] = embeddings

        index.update(**kwargs)

    def create_index(self, index_name: str, **kwargs: Any):
        return pinecone.create_index(index_name, dimension=1536, metric="cosine")

    def delete_index(self, index_name: str, **kwargs: Any):
        pass
        # return pinecone.delete_index(index_name)

    def get_or_create_index(self, index_name: str, schema: str, **kwargs: Any):
        indexes = pinecone.list_indexes()
        if index_name not in indexes:
            self.create_index(index_name, **kwargs)
        return pinecone.Index(index_name)

    def delete_document(self, document_id: str, **kwargs: Any):
        index = pinecone.Index(kwargs["index_name"])
        index.delete(ids=[document_id])

    def get_document_by_id(self, index_name: str, document_id: str, content_key: str) -> Document:
        index = pinecone.Index(index_name)
        result = index.fetch(ids=[document_id])["vectors"][document_id].to_dict()

        data = result["metadata"].pop("data")
        return Document(content_key, data, result["metadata"], result["values"])

    def similarity_search(self, index_name: str, document_query: DocumentQuery, **kwargs) -> List[Tuple[int, float]]:
        index = pinecone.Index(index_name)
        response = index.query(
            top_k=1,
            include_values=False,
            include_metadata=True,
            vector=document_query.query
        )
        matches = response["matches"]
        return matches

    def hybrid_search(self, index_name: str, document_query: DocumentQuery, **kwargs) -> List[Tuple[int, float]]:
        return self.similarity_search(index_name, document_query, **kwargs)
