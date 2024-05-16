from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.llms import LlamaCpp
from langchain.agents import initialize_agent, AgentType

toolkit = GmailToolkit()

from langchain_community.tools.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)

# Can review scopes here https://developers.google.com/gmail/api/auth/scopes
# For instance, readonly scope is 'https://www.googleapis.com/auth/gmail.readonly'
credentials = get_gmail_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/"],
    client_secrets_file="credentials.json",
)
api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)

tools = toolkit.get_tools()
tools


# Load the LLaMA2 model
model_path = "llama-2-7b.Q4_0.gguf"
llm = LlamaCpp(model_path=model_path, max_tokens=2048, n_ctx=2048)

toolkit = GmailToolkit(llm=llm)
tools = toolkit.get_tools()

# Initialize the CHAT_ZERO_SHOT_REACT_DESCRIPTION agent
agent = initialize_agent(tools, llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# Create a Gmail draft
agent.invoke({
    "input": "create_gmail_draft for me to edit of a letter from the perspective of a sentient parrot"
    " who is looking to collaborate on some research with her"
    " estranged friend, a cat. Under no circumstances may you send_gmail_message, however."
})