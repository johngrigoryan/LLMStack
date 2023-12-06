import logging

from enum import Enum
from typing import List
from pydantic import Field
from asgiref.sync import async_to_sync

from llmstack.processors.providers.api_processor_interface import ApiProcessorInterface, ApiProcessorSchema

from llmstack.processors.providers.custom.new_chat import Chat
from llmstack.processors.providers.custom.openai_compl import Completion
from llmstack.processors.providers.custom.vectordb import init_pinecone

logger = logging.getLogger(__name__)


class FSMChatCompletionsModel(str, Enum):
    GPT_4 = "gpt-4-0613"
    GPT_32_K = "gpt-4-32k-0613"
    GPT_3_5 = "gpt-3.5-turbo-0613"
    GPT_3_5_16K = "gpt-3.5-turbo-16k"

    def __str__(self):
        return self.value


class FSMProcessorInput(ApiProcessorSchema):
    question: str = Field(..., description="Question to answer")


class FSMProcessorOutput(ApiProcessorSchema):
    answer: str = Field(..., description="Answer to the question",
                        widget="textarea")


class FSMProcessorConfiguration(ApiProcessorSchema):
    chat_model: FSMChatCompletionsModel = Field(
        default=FSMChatCompletionsModel.GPT_4,
        description="ID of the model to use in the chat response generation. Currently, only `gpt-3.5-turbo` and `gpt-4` are supported.",
        widget="customselect",
        advanced_parameter=True,
    )
    functions_model: FSMChatCompletionsModel = Field(
        default=FSMChatCompletionsModel.GPT_3_5,
        description="ID of the model to use in the variable extraction. Currently, only `gpt-3.5-turbo` and `gpt-4` are supported.",
        widget="customselect",
        advanced_parameter=True,
    )
    datasource: List[str] = Field(
        default=None,
        description="Datasources to use", widget="datasource", advanced_parameter=False,
    )
    topic_is_not_found: str = Field(
        default="Sorry, but I cannot help you with this topic",
        widget="textarea", advanced_parameter=True,
        description="Predefined message when the topic has not been found in the datasource.")
    unresolved_issues: str = Field(
        default="There are unresolved issues, would you like to resolve them now?",
        widget="textarea", advanced_parameter=True,
        description="Predefined message to remind to the user that there are unresolved issues"
    )
    resolve_now_question: str = Field(
        default="Do you want to fix the issue right now or would like to finish the installation guide first?",
        widget="textarea", advanced_parameter=True,
        description="Predefined message to ask the user whether he wants to resolve mentioned issue now"
    )
    issue_has_been_resolved: str = Field(
        default="Congrats! The issue has been resolved, let's go back to the installation",
        widget="textarea", advanced_parameter=True,
        description="Predefined message to aware user that his issue has been resolved and they can return to the main guide"
    )


init_pinecone("gcp-starter", "8f7fd7b3-ed9a-4d2f-8de5-4480a2539acb")


class FSMProcessor(ApiProcessorInterface[FSMProcessorInput, FSMProcessorOutput, FSMProcessorConfiguration]):
    """
    FSM processor
    """

    def process_session_data(self, session_data):
        config = self._config.dict()
        self._chat_history = session_data["chat_history"] if "chat_history" in session_data else [
        ]
        self._issues = session_data["issues"] if "issues" in session_data else []
        self._current_state = session_data.get("current_state", "analyze")
        self._variables = session_data.get("variables", None)
        self._current_step = session_data.get("current_step", None)
        self._current_issue = session_data.get("current_issue", None)
        self._current_guide = session_data.get("current_guide", None)
        self._current_issue_guide = session_data.get("current_issue_guide", None)
        datasources = config.pop("datasource")
        print(datasources)
        self._chat = Chat("imea-index",
                          functions_model=config.pop("functions_model"),
                          chat_model=config.pop("chat_model"),
                          messages=self._chat_history,
                          issues=self._issues,
                          current_step=self._current_step,
                          current_guide=self._current_guide,
                          current_issue=self._current_issue,
                          current_issue_guide=self._current_issue_guide,
                          variables=self._variables,
                          default_messages=config,
                          data_ids=datasources)
        self._chat.state = self._current_state
        api_key = self._env["openai_api_key"]
        if api_key is None:
            raise Exception("No openai key provided")

        self._chat.llm_compl = Completion(api_key)

    def session_data_to_persist(self) -> dict:
        return {"chat_history": self._chat_history, "current_state": self._current_state,
                "current_step": self._current_step, "current_issue": self._current_issue,
                "current_guide": self._current_guide, "variables": self._variables, "issues": self._issues,
                "current_issue_guide": self._current_issue_guide}

    @staticmethod
    def name() -> str:
        return "FSM"

    @staticmethod
    def slug() -> str:
        return "fsm"

    @staticmethod
    def description() -> str:
        return "Conversation based on our custom algorithm"

    @staticmethod
    def provider_slug() -> str:
        return "custom"

    def process(self) -> dict:
        output_stream = self._output_stream

        answer = self._chat.run(self._input.question)
        async_to_sync(output_stream.write)(
            FSMProcessorOutput(answer=answer),
        )

        self._chat_history.append(
            {"role": "user", "content": self._input.question},
        )
        self._chat_history.append(
            {"role": "assistant", "content": answer},
        )

        output = output_stream.finalize()

        self._current_state = self._chat.current_state()
        self._current_guide = self._chat.current_guide
        self._current_issue = self._chat.current_issue
        self._current_issue_guide = self._chat.current_issue_guide
        self._variables = self._chat.variables
        self._issues = self._chat.issues
        self._current_step = self._chat.current_step

        return output
