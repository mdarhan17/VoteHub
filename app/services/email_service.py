import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_otp_email(to_email, otp):
    sender_email = os.getenv("MAIL_USERNAME")
    app_password = os.getenv("MAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        return False, "MAIL_USERNAME or MAIL_APP_PASSWORD missing in .env"

    subject = "VoteHub OTP Verification"

    html_body = f"""
    <html>
    <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;">
        <div style="max-width:560px;margin:40px auto;background:#ffffff;border-radius:20px;padding:32px;box-shadow:0 18px 45px rgba(15,23,42,0.12);">
            <h2 style="color:#2563eb;margin-bottom:8px;">VoteHub OTP Verification</h2>
            <p style="color:#334155;font-size:15px;">Hello,</p>
            <p style="color:#334155;font-size:15px;">Use the OTP below to verify your VoteHub account.</p>

            <div style="background:#eef4ff;border-radius:16px;padding:22px;text-align:center;margin:24px 0;">
                <h1 style="letter-spacing:8px;color:#0f172a;margin:0;font-size:34px;">{otp}</h1>
            </div>

            <p style="color:#64748b;font-size:14px;">This OTP is valid for 10 minutes.</p>
            <p style="color:#64748b;font-size:13px;">If you did not request this, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = to_email
    message.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to_email, message.as_string())
        server.quit()
        return True, "OTP sent successfully"
    except Exception as e:
        return False, str(e)
