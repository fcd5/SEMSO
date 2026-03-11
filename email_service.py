import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "usershelter702@gmail.com"
SMTP_PASS = "iwgy dvmr vtmh grzr"  # 16碼 App Password

def send_email(email, coin, alert_type, exchanges, target_price):
    subject = "SEMSO Price Alert"

    exchange_text = ""
    for ex, price in exchanges:
        exchange_text += f"{ex}: ${price}\n"

    body = f"""
SEMSO Oracle Alert

幣種: {coin}
買入/賣出: {alert_type}
當初設定的價格: ${target_price}

以下為達成條件的交易所和其價格:

{exchange_text}

"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL] sent to {email}")
    except Exception as e:
        print("[EMAIL ERROR]", e)