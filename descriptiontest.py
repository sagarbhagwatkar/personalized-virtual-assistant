import os
import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from googleapiclient.discovery import build
import base64
from cleantext import clean

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

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Function to extract text from a Word file
def extract_text_from_docx(docx_file):
    text = ""
    doc = Document(docx_file)
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

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
def get_llm_response(form_input, job_description, resume_text, email_sender, email_recipient, email_style, email_recipient_name, email_subject):
    service = get_gmail_service()

    llm = Ollama(model="llama3")
    
    # Clean the resume text
    resume_text = clean(resume_text, lower=True, no_line_breaks=True, no_punct=True, lang="en")
    
    # Template for building the PROMPT
    template ="""
    Write an email on the topic: "{email_topic}" with {style} style, ensuring grammatically correct and complete sentences. Sentences should not be broken in the middle and should flow naturally.

    Explain briefly my skills and experience from "{resume_text}", also add only those requirements that I fulfill from the job description of the company "{job_description}" with proof of experience from the resume, do not do hallucination and do not mention false details that I don't fulfill from my resume.
    
    **From:** {sender}
    **To:** {recipient}
    """

    # Creating the final PROMPT
    prompt = PromptTemplate(
        input_variables=["style", "email_topic", "sender", "subject", "recipient", "job_description", "resume_text"],
        template=template
    )
  
    # Generating the response using LLM
    email_body = llm(prompt.format(email_topic=form_input, sender=email_sender, recipient=email_recipient_name, subject=email_subject, style=email_style, resume_text=resume_text, job_description=job_description))
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
    resume_file = st.file_uploader("Upload Resume (PDF or Word)", type=["pdf", "docx"])
    job_description = st.text_area('Enter the job description')
    submit = st.button("Generate")

# Main content
if submit:
    st.subheader("Email Preview")
    if resume_file is not None:
        if resume_file.type == "application/pdf":
            resume_text = extract_text_from_pdf(resume_file)
        elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            resume_text = extract_text_from_docx(resume_file)
        else:
            st.error("Unsupported file format. Please upload either a PDF or Word file.")
            st.stop()
    else:
        # If no file is uploaded, set resume_text to an empty string
        resume_text = ""
    
    draft_id, draft_content = get_llm_response(form_input, job_description, resume_text, email_sender, email_recipient, email_style, email_recipient_name, email_subject)
    st.success(f'Draft created with ID: {draft_id}')
    st.info("Draft Content:")
    st.code(draft_content)  # Display draft message content
