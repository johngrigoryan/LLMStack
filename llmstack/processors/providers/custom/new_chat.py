import fsm
import json
import time

from llmstack.processors.providers.custom.temp_prompts import analyze_prompt, input_prompt, guides_prompt, \
    issues_prompt, switch_prompt
from llmstack.processors.providers.custom.functions_openai import create_openai_function_schema, Property, Type
from llmstack.processors.providers.custom.functions_default import INPUT_STATE_FUNCTION_DESCRIPTION, \
    INPUT_STATE_FUNCTION_NAME, \
    GUIDE_STATE_FUNCTION_DESCRIPTION, GUIDE_STATE_FUNCTION_NAME, SWITCH_STATE_FUNCTION_DESCRIPTION, \
    SWITCH_STATE_FUNCTION_NAME, ISSUES_STATE_FUNCTION_NAME, ISSUES_STATE_FUNCTION_DESCRIPTION, \
    ANALYZE_STATE_FUNCTION_NAME, ANALYZE_STATE_FUNCTION_DESCRIPTION
from llmstack.processors.providers.custom.vectordb import similarity_search


class Chat(fsm.FiniteStateMachineMixin):
    state_machine = {
        "analyze": ("input", "analyze"),
        "input": ("input", "guide"),
        "guide": ("guide", "switch", "input"),
        "switch": ("guide", "issues"),
        "issues": ("guide", "issues")
    }

    state = "analyze"

    llm_compl = None

    def __init__(self, index_name, functions_model, chat_model, issues, messages, current_guide, variables,
                 current_step, current_issue, current_issue_guide, default_messages, data_ids):
        super().__init__()
        self.issues = issues
        self.messages = messages
        self.vectordb_index_name = index_name
        self.functions_model = functions_model
        self.chat_model = chat_model
        self.current_issue = current_issue
        self.current_issue_guide = current_issue_guide
        self.current_step = current_step
        self.current_guide = current_guide
        self.variables = variables
        self.topic_is_not_found = default_messages["topic_is_not_found"]
        self.unresolved_issues = default_messages["unresolved_issues"]
        self.resolve_now_question = default_messages["resolve_now_question"]
        self.issue_has_been_resolved = default_messages["issue_has_been_resolved"]
        self.ids = data_ids

    def add_message(self, message, role):
        self.messages.append({"role": role, "content": message})

    @staticmethod
    def extract_vars_analyze_state(args):
        result = json.loads(args)
        if result["topic"] in ("None", ""):
            result["topic"] = None
        return result

    @staticmethod
    def extract_vars_input_state(args):
        print(args)
        result = json.loads(args)
        for k in result:
            if result[k] in ("None", ""):
                result[k] = None
            try:
                result[k] = int(result[k])
            except:
                pass
        return result

    @staticmethod
    def extract_vars(args):
        return json.loads(args)

    def analyze_state_perform(self, new_user_message):
        functions = create_openai_function_schema(
            [Property(variable_name="topic",
                      description="The short description of the guide's topic. Put it None if no guide or help is given by user",
                      variable_type=Type.Str)], ANALYZE_STATE_FUNCTION_NAME, ANALYZE_STATE_FUNCTION_DESCRIPTION)
        args = self.llm_compl.generate_json_with_functions(analyze_prompt, functions, self.messages, new_user_message,
                                                           model=self.functions_model)
        result = self.extract_vars_analyze_state(args)
        print(result)
        user_query = result["topic"]
        if user_query is not None:
            embedding = self.llm_compl.get_embedding(user_query)
            data = similarity_search(self.vectordb_index_name, embedding, self.ids)
            if data is None:
                return self.topic_is_not_found
            self.current_guide = data.pop("data")
            self.variables = data
            self.change_state("input")
            return self.input_state_perform(new_user_message)
        return self.llm_compl.generate_chat_response(analyze_prompt, self.messages, new_user_message,
                                                     model=self.chat_model)

    def input_state_perform(self, new_user_message):
        properties = []
        prompt = input_prompt
        for variable, values in self.variables.items():
            value = values[0]
            desc = values[1]
            prompt = prompt + desc

            if isinstance(value, bool):
                enum_ = [0, 1, -1]
                type_ = "integer"
            else:
                enum_ = None
                type_ = Type(type(value).__name__)
            properties.append(
                Property(variable_name=variable, description=desc, variable_type=type_, enum_=enum_))
        functions = create_openai_function_schema(properties, INPUT_STATE_FUNCTION_NAME,
                                                  INPUT_STATE_FUNCTION_DESCRIPTION)
        args = self.llm_compl.generate_json_with_functions(prompt, functions, self.messages, new_user_message,
                                                           model=self.functions_model)
        result = self.extract_vars_input_state(args)
        print(result)
        for variable in self.variables:
            if result[variable] is None or result[variable] == -1:
                return self.llm_compl.generate_chat_response(prompt, self.messages, new_user_message,
                                                             model=self.chat_model)
        if self.check_variables(result, self.variables):
            self.change_state("guide")
            return self.guide_state_perform(self.messages, "Let's start")
        return self.topic_is_not_found

    def guide_state_perform(self, messages, new_user_message):
        prompt = guides_prompt.format(self.current_guide)
        if self.current_step:
            prompt += f"You are at the step: {self.current_step}"

        functions = create_openai_function_schema([
            Property(variable_name="current_step",
                     description="the current step of the guide. set to -1 in case when the last "
                                 "step of the guide has been successfully finished",
                     variable_type=Type.Int),
            Property(variable_name="issues",
                     description="whether the user mentioned an issue or troubleshooting",
                     variable_type=Type.Bool)
        ], GUIDE_STATE_FUNCTION_NAME, GUIDE_STATE_FUNCTION_DESCRIPTION)

        args = self.llm_compl.generate_json_with_functions(prompt, functions, messages, new_user_message,
                                                           model=self.functions_model)
        result = self.extract_vars(args)
        print(result)
        self.current_step = result["current_step"]
        if self.current_step == -1:
            if self.issues:
                self.current_issue = self.issues[0]
                self.change_state("switch")
                return self.unresolved_issues
            self.change_state("input")
            self.current_step = None
            self.messages.clear()
            return None
        issues = result["issues"]
        if issues:
            self.current_issue = new_user_message
            self.change_state("switch")
            return self.resolve_now_question
        return self.llm_compl.generate_chat_response(prompt, messages, new_user_message, model=self.chat_model)

    def switch_state_perform(self, new_user_message):
        functions = create_openai_function_schema([Property(variable_name="resolve_now",
                                                            description="whether the user wants to resolve the issue now or not",
                                                            variable_type=Type.Bool)],
                                                  SWITCH_STATE_FUNCTION_NAME, SWITCH_STATE_FUNCTION_DESCRIPTION)

        args = self.llm_compl.generate_json_with_functions(switch_prompt.format(self.current_issue),
                                                           functions, self.messages[-2:], new_user_message,
                                                           model=self.functions_model)
        result = self.extract_vars(args)
        print(result)
        if not result["resolve_now"]:
            self.change_state("guide")
            if self.current_step == -1:
                self.issues.clear()
            else:
                self.issues.append(self.current_issue)
            self.current_issue = None
            return self.guide_state_perform(list(), new_user_message)
        else:
            self.change_state("issues")
            embedding = self.llm_compl.get_embedding(self.current_issue)
            self.current_issue_guide = similarity_search(self.vectordb_index_name, embedding, self.ids)["data"]
            content = self.llm_compl.generate_chat_response(issues_prompt.format(self.current_issue_guide),
                                                            self.messages[-10:], self.current_issue,
                                                            model=self.chat_model)
            return content

    def issues_state_perform(self, new_user_message):
        prompt = issues_prompt.format(self.current_issue_guide)
        functions = create_openai_function_schema([
            Property(variable_name="is_resolved",
                     description="whether the issue has been successfully fixed",
                     variable_type=Type.Bool),
            Property(variable_name="is_terminated",
                     description="whether the user stops the troubleshooting and wants to do something else",
                     variable_type=Type.Bool)
        ], ISSUES_STATE_FUNCTION_NAME, ISSUES_STATE_FUNCTION_DESCRIPTION)

        args = self.llm_compl.generate_json_with_functions(prompt, functions,
                                                           self.messages[-10:], new_user_message,
                                                           model=self.functions_model)
        result = self.extract_vars(args)
        print(result)
        is_resolved = result["is_resolved"]
        is_terminated = result["is_terminated"]
        if is_resolved and not is_terminated:
            self.change_state("guide")
            self.current_issue = None
            return self.issue_has_been_resolved
        if is_terminated:
            if not is_resolved:
                self.issues.append(self.current_issue)
            self.current_issue = None
            self.change_state("guide")
            return self.guide_state_perform(self.messages[-2:], new_user_message)

        return self.llm_compl.generate_chat_response(prompt, self.messages[-10:], new_user_message,
                                                     model=self.chat_model)

    def perform(self, new_user_message):
        curr_state = self.current_state()
        if curr_state == "analyze":
            return self.analyze_state_perform(new_user_message)
        if curr_state == "input":
            return self.input_state_perform(new_user_message)
        elif curr_state == "guide":
            return self.guide_state_perform(self.messages[-6:], new_user_message)
        elif curr_state == "switch":
            return self.switch_state_perform(new_user_message)
        elif curr_state == "issues":
            return self.issues_state_perform(new_user_message)

    def run(self, query):
        print(self.current_state())
        start = time.time()
        answer = self.perform(query)
        print(answer)
        end = time.time() - start
        print(end)

        return answer

    @staticmethod
    def check_variables(extracted_values, default_values):
        for variable, extracted_value in extracted_values.items():
            if isinstance(default_values[variable][0], str):
                if extracted_value.lower().find(default_values[variable][0].lower()) == -1:
                    return False
            else:
                if bool(extracted_value) != default_values[variable][0]:
                    return False
        return True

# if __name__ == '__main__':
#     chat = Chat()
#     chat.llm_compl = Completion()
#     while True:
#         query = input("Your query: ")
#         if query.lower() == 'q':
#             break
#         answer = chat.run(query)
#         print(answer)
