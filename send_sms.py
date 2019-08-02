import os
from twilio.rest import Client

account_sid = os.environ.get('TWILIO_ACC_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

message = client.messages.create(body='Let\'s fix Goodreads!', from_='+19373066025', to='+19373087294')

print(message.sid)
