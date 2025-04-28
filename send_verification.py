from smtplib import SMTP
from email.message import EmailMessage


class Smtp_verification():

    def __init__(self, mail_username, mail_port, mail_password, mail_host):
        self.mail_username = mail_username
        self.mail_password = mail_password
        self.mail_host= mail_host
        self.mail_port = mail_port

    def send_code(self, message, to_address):
        msg = EmailMessage()
        msg['Subject'] = 'Confirm Your Account'
        msg['From'] = self.mail_username
        msg['To'] = to_address
        msg.set_content(message)

        with SMTP(host=self.mail_host, port=self.mail_port) as server:
            server.starttls()
            server.login(user=self.mail_username, password=self.mail_password)
            server.send_message(msg)
