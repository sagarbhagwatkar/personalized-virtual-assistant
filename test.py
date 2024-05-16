from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.llms import LlamaCpp
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import PromptTemplate

# Initialize GmailToolkit
toolkit = GmailToolkit()

# Get Gmail credentials and build resource service
from langchain_community.tools.gmail.utils import build_resource_service, get_gmail_credentials

credentials = get_gmail_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/"],
    client_secrets_file="credentials.json",
)
api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)

# Load the LLaMA2 model
model_path = "llama-2-7b.Q4_0.gguf"
llm = LlamaCpp(model_path=model_path, max_tokens=2048, n_ctx=2048)

# Initialize GmailToolkit with LLaMA model
toolkit = GmailToolkit(llm=llm)

# Get tools
tools = toolkit.get_tools()

# Define prompt template for the LLaMA model
prompt_template = PromptTemplate.from_template("Create a Gmail draft with the following fields: Subject: 'Research Collaboration', Body: 'Hi this is a langchain test email', To: 'tewjaswict@gmail.com'. Do not send the email.")

# Initialize agent with tools, LLaMA model, and prompt template
agent = initialize_agent(tools, llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, prompt_template=prompt_template, verbose=True)

# Create a Gmail draft using the agent
agent.invoke({"input": "create_gmail_draft"})

