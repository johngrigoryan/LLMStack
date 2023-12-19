<p align="center">
  <a href="https://llmstack.ai"><img src="https://llmstack.ai/img/llmstack-logo-light-white-bg.svg" alt="LLMStack" width="500px"></a>
</p>
<p align="center">
    <em>LLMStack is a no-code platform for building generative AI applications, chatbots, agents and connecting them to your data and business processes.</em>
</p>
<p align="center">
    <a href="https://llmstack.ai/docs/getting-started/introduction#quickstart" target="_blank">Quickstart</a> | <a href="https://llmstack.ai/docs/" target="_blank">Documentation</a> | <a href="trypromptly.com" target="_blank">Promptly</a>
</p>

## Getting Started

**_Check out our Cloud offering at [Promptly](https://trypromptly.com) or follow the instructions below to deploy LLMStack on your own infrastructure._**

LLMStack deployment comes with a default admin account whose credentials are `admin` and `promptly`. _Be sure to change the password from admin panel after logging in_.

### Installation

> If you are on windows, please use WSL2 (Windows Subsystem for Linux) to install LLMStack. You can follow the instructions [here](https://docs.microsoft.com/en-us/windows/wsl/install-win10) to install WSL2. Once you are in a WSL2 terminal, you can install LLMStack using the above command.

You need to clone the repository to your device.

```sh
git clone git@github.com:johngrigoryan/LLMStack.git
```

Above commands will install and start LLMStack. It will create `.llmstack` in your home directory and places the database and config files in it when run for the first time. Once LLMStack is up and running, it should automatically open your browser and point it to [localhost:3000](http://localhost:3000).

> You can add your own keys to providers like OpenAI, Cohere, Stability etc., from Settings page. If you want to provide default keys for all the users of your LLMStack instance, you can add them to the `~/.llmstack/config` file.

## Running locally and Development

```bash
cd llmstack/client
npm install
npm run build
cd ../..
python3 -m pip install poetry
poetry install
poetry shell
llmstack
```

> You can skip running `npm install` and `npm run build` if you have already built the client before

For frontend development, you can use `REACT_APP_API_SERVER=localhost:3000 npm start` to start the development server in client directory. You can also use `npm run build` to build the frontend and serve it from the backend server.

To update documentation, make changes to `web/docs` directory and run `npm run build` in web directory to build the documentation. You can use `npm start` in web directory to serve the documentation locally.


## Docker
To build the docker image

```bash
./build.sh
```
To run the container

```bash
docker run -d -p 3000:3000 llmstack
```

Once the docker image is built and running, you can access LLMStack on [localhost:3000](http://127.0.0.1:3000).

The container will create a default user with username **admin** and password **promptly**. If you want to change the credentials of the default user, before building the image, go to the **.llmstack/config** file, and update the fields **admin_username** and **admin_password**. Once the docker image has been built, the credentials can be changed from the [admin page](http://127.0.0.1:3000/admin/).

## Features

**🔗 Chain multiple models**: LLMStack allows you to chain multiple LLMs together to build complex generative AI applications.

**📊 Use generative AI on your Data**: Import your data into your accounts and use it in AI chains. LLMStack allows importing various types (_CSV, TXT, PDF, DOCX, PPTX etc.,_) of data from a variety of sources (_gdrive, notion, websites, direct uploads etc.,_). Platform will take care of preprocessing and vectorization of your data and store it in the vector database that is provided out of the box.

**🛠️ No-code builder**: LLMStack comes with a no-code builder that allows you to build AI chains without any coding experience. You can chain multiple LLMs together and connect them to your data and business processes.

**☁️ Deploy to the cloud or on-premise**: LLMStack can be deployed to the cloud or on-premise. You can deploy it to your own infrastructure or use our cloud offering at [Promptly](https://trypromptly.com).

**🚀 API access**: Apps or chatbots built with LLMStack can be accessed via HTTP API. You can also trigger your AI chains from **_Slack_** or **_Discord_**.

**🏢 Multi-tenant**: LLMStack is multi-tenant. You can create multiple organizations and add users to them. Users can only access the data and AI chains that belong to their organization.

## What can you build with LLMStack?

Using LLMStack you can build a variety of generative AI applications, chatbots and agents. Here are some examples:

**📝 Text generation**: You can build apps that generate product descriptions, blog posts, news articles, tweets, emails, chat messages, etc., by using text generation models and optionally connecting your data. Check out this [marketing content generator](https://trypromptly.com/app/50ee8bae-712e-4b95-9254-74d7bcf3f0cb) for example

**🤖 Chatbots**: You can build chatbots trained on your data powered by ChatGPT like [Promptly Help](https://trypromptly.com/app/f4d7cb50-1805-4add-80c5-e30334bce53c) that is embedded on Promptly website

**🎨 Multimedia generation**: Build complex applications that can generate text, images, videos, audio, etc. from a prompt. This [story generator](https://trypromptly.com/app/9d6da897-67cf-4887-94ec-afd4b9362655) is an example

**🗣️ Conversational AI**: Build conversational AI systems that can have a conversation with a user. Check out this [Harry Potter character chatbot](https://trypromptly.com/app/bdeb9850-b32e-44cf-b2a8-e5d54dc5fba4)

**🔍 Search augmentation**: Build search augmentation systems that can augment search results with additional information using APIs. Sharebird uses LLMStack to augment search results with AI generated answer from their content similar to Bing's chatbot

**💬 Discord and Slack bots**: Apps built on LLMStack can be triggered from Slack or Discord. You can easily connect your AI chains to Slack or Discord from LLMStack's no-code app editor. Check out our [Discord server](https://discord.gg/3JsEzSXspJ) to interact with one such bot.

## Administration

Login to [http://localhost:3000/admin](http://localhost:3000/admin) using the admin account. You can add users and assign them to organizations in the admin panel.

## Cloud Offering

Check out our cloud offering at [Promptly](https://trypromptly.com). You can sign up for a free account and start building your own generative AI applications.

## Documentation

Check out our documentation at [llmstack.ai/docs](https://llmstack.ai/docs/) to learn more about LLMStack.
