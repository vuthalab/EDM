import smtplib, ssl
from email.message import EmailMessage
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

##Function to Read in email message from text file
#def read_email(filename):
 #   with open(filename, 'r',encoding ='utf-8') as email_file:
  #      email_file_contents = email_file.read()
   #     return Template(email_file_contents)



##Function to send email messge
def send_mail(message):
    port = 465 #gmail server port that allows for tls secure transfer
    my_address = 'celinedmbaf@gmail.com' #email address for edm expeirment
    to_email ="camilojocasan@gmail.com" # recipient email address
    password = "Fallingintoyou" #Celine's email password
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context = context) as server:
        server.ehlo()
        server.login(my_address,password)
        server.sendmail(my_address, to_email, message)
        server.quit()
    return 0
# to add headers, attachments, and other elements to the email, create a MIMEMultipart() object