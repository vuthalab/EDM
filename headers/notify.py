import os, time
import requests


#with open('.mailgun.key', 'r') as f:
#    API_KEY = f.read().strip()


cache = {}

def send_email(
    subject: str, body: str,
    cooldown: float = 12,
    high_priority: bool = True 
):
    return
    """
    Sends a notification email.
    Does nothing if an email with the same subject was sent
    within the last `cooldown` hours.
    """

    # Prevent spam (limit to 1 email per 10 minutes, for each subject)
    if subject in cache and time.time() - cache[subject] < 3600 * cooldown: return

    if high_priority:
        recipients = [
            'samuelj.li@protonmail.com',
#            'camilo.castellanossanchez@mail.utoronto.ca',
#            'rhys.anderson@mail.utoronto.ca',
        ]
    else:
        recipients = ['samuelj.li@protonmail.com']


    try:
        requests.post(
            'https://api.mailgun.net/v3/samuelj.li/messages',
            auth=('api', API_KEY),
            data={
                'from': 'EDM Experiment <edm@samuelj.li>',
                'to': recipients,
                'subject': subject,
                'text': body,
            }
        )
        print(f'Sent email: {subject}')
        cache[subject] = time.time()
    except Exception as e:
        print(e)
