
import os
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from googleapiclient.discovery import build
import base64

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


# Function to create a draft in Gmail
def create_draft(service, sender, recipient, subject, body):
    # Construct the email message
    message = f'Subject: {subject}\nFrom: {sender}\nTo: {recipient}\n\n{body}'
    # Encode the email message in Base64 format
    raw_message = base64.urlsafe_b64encode(message.encode()).decode()

    # Create the draft
    draft = {'message': {'raw': raw_message}}
    draft = service.users().drafts().create(userId='me', body=draft).execute()
    draft_id = draft['id']
    print(f'Draft created with ID: {draft_id}')
    return draft_id, message

# Function to get the response back from LLM
def get_llm_response(form_input, email_sender, email_recipient, email_style, email_recipient_name, email_subject):
    service = get_gmail_service()

    llm = Ollama(model="llama3")
    
    # Template for building the PROMPT
    template ="""
    Write an email on the topic: "{email_topic}" with {style} style, ensuring grammatically correct and complete sentences. Sentences should not be broken in the middle and should flow naturally.
    
    **From:** {sender}
    **To:** {recipient}
    """

    # Creating the final PROMPT
    prompt = PromptTemplate(
        input_variables=["style", "email_topic", "sender", "subject", "recipient"],
        template=template
    )
  
    # Generating the response using LLM
    email_body = llm(prompt.format(email_topic=form_input, sender=email_sender, recipient=email_recipient_name, subject=email_subject, style=email_style))
    print(email_body)

    # Create a draft with the email content
    draft_id, draft_content = create_draft(service, email_sender, email_recipient, email_subject, email_body)
    return draft_id, draft_content

# Streamlit app
st.set_page_config(page_title="Generate Emails",
                    page_icon='✍️',
                    layout='centered',
                    initial_sidebar_state='collapsed')

# Header
st.title("Generate Email ✍️")

# Sidebar inputs
with st.sidebar:
    st.header("Email Details")
    form_input = st.text_area('Enter the email topic', height=275)
    email_subject = st.text_input('Email Subject')
    email_sender = st.text_input('Sender Name')
    email_recipient = st.text_input('Recipient Email')
    email_recipient_name = st.text_input('Recipient Name')
    email_style = st.selectbox('Writing Style',
                                ('Formal', 'Informal', 'Angry', 'Appreciating', 'Not Satisfied', 'Neutral'),
                                    index=0)
    submit = st.button("Generate")

# Main content
if submit:
    st.subheader("Email Preview")
    draft_id, draft_content = get_llm_response(form_input, email_sender, email_recipient, email_style, email_recipient_name, email_subject)
    st.success(f'Draft created with ID: {draft_id}')
    st.info("Draft Content:")
    st.code(draft_content)  # Display draft message content



