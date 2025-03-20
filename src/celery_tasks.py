from src.celery_worker import celery_app
from src.mail import mail
import asyncio

@celery_app.task
def send_email_async(message):
    # Run the async email-sending function in the event loop
    asyncio.run(mail.send_message(message))