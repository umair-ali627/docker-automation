from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from decouple import config
import logging

logger = logging.getLogger(__name__)

def test_sendgrid():
    message = Mail(
        from_email=config('SENDGRID_FROM_EMAIL'),
        to_emails='sheikhahtasham007@gmail.com',
        subject='Test Email from ConvoiAI',
        plain_text_content='This is a test email.'
    )
    try:
        sg = SendGridAPIClient(config('SENDGRID_API_KEY'))
        response = sg.send(message)
        logger.info(f"SendGrid response: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"SendGrid error: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_sendgrid()
    