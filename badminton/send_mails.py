import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sender_email = "luyansasc@gmail.com"
receiver_emails = ["luyansasc@gmail.com"]


def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    # noinspection SpellCheckingInspection
    server.login(sender_email, os.getenv("GMAIL_PWD"))
    server.sendmail(sender_email, receiver_emails, msg.as_string())
    server.quit()

if __name__ == "__main__":
    send_email("Test Subject", "This is a test email body.")