import openai


class Completion:
    def __init__(self, openai_api_key, frequency_penalty=0, presence_penalty=0, temperature=0,
                 top_p=1):
        openai.api_key = openai_api_key
        self.freq_penalty = frequency_penalty
        self.pres_penalty = presence_penalty
        self.temperature = temperature
        self.top_p = top_p

    def generate_chat_response(self, system_prompt, prev_messages, user_message, model="gpt-4-0613"):
        messages = [{"role": "system", "content": system_prompt}] + prev_messages + [
            {"role": "user", "content": user_message}]
        response = openai.chat.completions.create(model=model,
                                                  frequency_penalty=self.freq_penalty,
                                                  presence_penalty=self.pres_penalty,
                                                  temperature=self.temperature,
                                                  top_p=self.top_p,
                                                  messages=messages)

        return response.choices[0].message.content

    def generate_json_with_functions(self, system_prompt, functions, prev_messages, user_message,
                                     model="gpt-3.5-turbo-0613"):
        messages = [{"role": "system", "content": system_prompt}] + prev_messages + [
            {"role": "user", "content": user_message}]
        response = openai.chat.completions.create(model=model,
                                                  frequency_penalty=self.freq_penalty,
                                                  presence_penalty=self.pres_penalty,
                                                  temperature=self.temperature,
                                                  top_p=self.top_p,
                                                  messages=messages,
                                                  functions=functions,
                                                  function_call={"name": functions[0]["name"]})

        return response.choices[0].message.function_call.arguments

    @staticmethod
    def get_embedding(text):
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        embeddings = response.data[0].embedding

        return embeddings
