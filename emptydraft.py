import os
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from langchain.prompts import PromptTemplate
from langchain.llms import CTransformers
from googleapiclient.discovery import build


# Function to authenticate with Gmail API and get service
def get_gmail_service():
    SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

    # Load or create Gmail API credentials
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build and return the Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    return service

# Function to get the response back from LLM
def get_llm_response(form_input, email_sender, email_recipient, email_style):
    service = get_gmail_service()

    llm = CTransformers(model="llama-2-7b.Q4_0.gguf",     
                    model_type='llama',
                    config={'max_new_tokens': 256,
                            'temperature': 0.01})
    
    # Template for building the PROMPT
    template = """
    Write a email with {style} style and includes topic: {email_topic}.\n\nSender: {sender}\nRecipient: {recipient}\n\nEmail Text:\n\n
    """

    # Creating the final PROMPT
    prompt = PromptTemplate(
        input_variables=["style", "email_topic", "sender", "recipient"],
        template=template
    )
  
    # Generating the response using LLM
    response = llm(prompt.format(email_topic=form_input, sender=email_sender, recipient=email_recipient, style=email_style))
    print(response)

    return response

# Streamlit app
st.set_page_config(page_title="Generate Emails",
                    page_icon='📧',
                    layout='centered',
                    initial_sidebar_state='collapsed')
st.header("Generate Emails 📧")

form_input = st.text_area('Enter the email topic', height=275)

# Creating columns for the UI - To receive inputs from user
col1, col2, col3 = st.columns([10, 10, 5])
with col1:
    email_sender = st.text_input('Sender Name')
with col2:
    email_recipient = st.text_input('Recipient Name')
with col3:
    email_style = st.selectbox('Writing Style',
                                    ('Formal', 'Appreciating', 'Not Satisfied', 'Neutral'),
                                       index=0)

submit = st.button("Generate")

# When 'Generate' button is clicked, execute the below code
if submit:
    st.write(get_llm_response(form_input, email_sender, email_recipient, email_style))
