import os, time
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

cache = {}

def send_email(subject: str, body: str, cooldown: float = 12):
    """
    Sends a notification email.
    Does nothing if an email with the same subject was sent
    within the last `cooldown` hours.
    """

    # Prevent spam (limit to 1 email per 10 minutes, for each subject)
    if subject in cache and time.time() - cache[subject] < 3600 * cooldown: return

    message = Mail(
        from_email='edm@samuelj.li',
        to_emails=[
            'samuelj.li@protonmail.com',
            'camilo.castellanossanchez@mail.utoronto.ca',
            'rhys.anderson@mail.utoronto.ca',
        ],
        subject=subject,
        html_content=body,
    )

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f'Sent email: {subject}')
        cache[subject] = time.time()
    except Exception as e:
        print(e.message)

#send_email('Test Message', 'Test of the EDM email notifications. Let me know if you got the mail.')
