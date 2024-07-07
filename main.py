from pathlib import Path
from google.oauth2.service_account import Credentials
from langchain_groq import ChatGroq
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from email.mime.text import MIMEText
import smtplib
import gspread
import json


# ================ LOAD ENVIRONMENT VARIABLE ===========================
from dotenv import load_dotenv
import os
load_dotenv()


# =========================== DEFINE GOOGLE SHEET_ID, SHEET_NAME, SUBJECT AND PROMPT TEMPLATE ===========================
SHEET_ID = "1XMb1WLnwj4_-oGw497DBLS16BGU96Walj7dlHAAW5Oc"
SHEET_NAME = "Sheet1"
SUBJECT = "Unlock AI Automation For You Business"
TEMPLATE = """
You are an AI chatbot assistant tasked with writing a personalized business email offering AI automation services to the following person:

Name: {name}
Bio: {bio}

The email should:

- Open with a friendly greeting and introduction, acknowledging the recipient's background and role
- Explain how your AI automation consulting services can benefit their business, based on their industry and needs
- Highlight your team's relevant expertise and experience implementing successful AI solutions
- Invite the recipient to schedule a consultation to discuss how AI can streamline their operations
- Close with a personalized call to action for the recipient to reach out and learn more

The tone should be professional yet personable, tailored to the recipient's background and position. Use clear, conversational language throughout. Proofread carefully for proper spelling, grammar, and formatting.

Please generate a 3-4 paragraph email that incorporates the provided information about the recipient.

My Information
Harun Jeylan
AI Automation Agency
Agencee
harunjeylanwako@gmail.com
"""


# =========================== GOOGLE SERVICE ACCOUNT CREDENTIAL ===========================
scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]


credentials = Credentials.from_service_account_file('google-sheet.json', scopes=scopes)


# =========================== GOOGLE SHEET ACCESS ===========================
client = gspread.authorize(credentials)

workbook = client.open_by_key(SHEET_ID)
sheet = workbook.worksheet(SHEET_NAME)

list_of_dicts = sheet.get_all_records()


# =========================== FILTERING KEYS ===========================
filter_criteria = ["name", "bio", "email"]
filtered_data = [{key: value for key, value in data.items() if key in filter_criteria} for data in list_of_dicts]


# =========================== WRITE AN EMAIL WITH AI ===========================
def write_email(data):
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama3-8b-8192"
    )
    prompt = PromptTemplate.from_template(TEMPLATE)
    runnable = LLMChain(prompt=prompt, llm=llm)
    result_dict = runnable.invoke(data)
    output_key = runnable.output_key
    result = result_dict[output_key]
    return result


# =========================== SEND AN EMAIL ===========================
def send_email(content, destination):
    sender_email = os.getenv("SENDER_EMAIL")
    smtp_server = os.getenv("SMTP_SERVER")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    
    success = False
    message = ""
    try:
        with smtplib.SMTP(smtp_server, timeout=10) as smtp:
            msg = MIMEText(content, 'plain')
            msg['Subject'] = SUBJECT
            msg['From'] = sender_email
            
            smtp.starttls()
            smtp.set_debuglevel(1)
            smtp.login(username, password)
            smtp.sendmail(sender_email, destination, msg.as_string())
            print("Email sent successfully!")
            success = True
            message = "Email sent successfully!"
            
    except TimeoutError:
        print("Timeout error: Could not connect to the SMTP server.")
        message = "Timeout error: Could not connect to the SMTP server."
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        message = f"SMTP error: {e}"
    return success, message      


# =========================== COMBINE ALL TOGETHER ===========================
def do_job(data_list, tasks):
    if len(data_list) > 0:
        data = data_list[0]
        
        print("Writing Email for:", data['email'] )
        
        content = write_email(data)
        
        if content:
            print("Sending Email for:", data['email'], "Content:", content )
            success, message = send_email(content, [data['email']])
            if success:
                print("Email Sent Successfully for:", data['email'] )
            else:
                print("Email Sent Feld for:", data['email'] )

            tasks.append({"email":data['email'], "message": message})
    
    if len(data_list) > 0:
        do_job(data_list[1:], tasks)
    
    return tasks


# =========================== RUN FLOW ===========================
if __name__ == "__main__":
    tasks = do_job(filtered_data, [])

    print(tasks)