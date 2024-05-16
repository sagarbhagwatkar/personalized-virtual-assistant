from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.llms import LlamaCpp
from langchain.agents.structured_chat.base import create_structured_chat_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import re
from langchain_core.output_parsers.base import BaseOutputParser

# Get Gmail credentials and build resource service
from langchain_community.tools.gmail.utils import build_resource_service, get_gmail_credentials

credentials = get_gmail_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/"],
    client_secrets_file="credentials.json",
)
api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)
tools = toolkit.get_tools()

# Load the LLaMA2 model
model_path = "llama-2-7b.Q4_0.gguf"
llm = LlamaCpp(model_path=model_path, max_tokens=2048, n_ctx=2048)

# Define prompt template for the LLaMA model
tools_description = "You have access to the following tools:\n\n" + "\n\n".join([f"{tool.name}: {tool.description}" for tool in tools])
tool_names = ", ".join([tool.name for tool in tools])

prompt_template = ChatPromptTemplate.from_messages([
    "Human: Here is the context:",
    "Human: Create a Gmail draft with the following fields: Subject: 'Research Collaboration', Body: 'Hi this is a langchain test email', To: 'sagarbhagwatkar51@gmail.com'. Save the draft in my Gmail account.",
    "Human: {agent_scratchpad}",
    f"Assistant: Here are the available tools:\n\n{tools_description}\n\nTool names: {tool_names}",
    "Human: Based on the context and available tools, save the create_gmail_draft to gmail account based on get_gmail_credentials",
    "Tools: {tools}",
    "Tool Names: {tool_names}"
])

class CustomOutputParser(BaseOutputParser):
    def __init__(self, regex_pattern, output_keys):
        self.regex_pattern = regex_pattern
        self.output_keys = output_keys

    async def parse(self, output: str) -> dict:
        parsed_output = {}
        for key, pattern in zip(self.output_keys, self.regex_pattern.split("|")):
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                parsed_output[key] = match.group()
        return parsed_output
    
# Define the regex components
regex_components = [
    r"(?i)(?=.*draft)(?=.*created)",
    r"(?i)(?=.*email)(?=.*sent)",
    # Add more regex components for other tools as needed
]

# Concatenate the regex components into a single string
regex_pattern = "|".join(regex_components)

# Create the custom output parser instance with the concatenated regex pattern
output_parser = CustomOutputParser(regex_pattern=regex_pattern, output_keys=["create_gmail_draft", "send_gmail_message"])
agent = create_structured_chat_agent(llm, tools, prompt_template, output_parser=output_parser)

# Create and save a Gmail draft using the agent
result = agent.invoke({"input": "create_gmail_draft", "intermediate_steps": []})
draft_id = result["output"]

# Use the create_gmail_draft tool to save the draft
create_draft_tool = next(tool for tool in tools if tool.name == "create_gmail_draft")
create_draft_tool.run(draft_id=draft_id)
