import json
import os
import logging
import urllib.request
import base64
import hashlib
import hmac
import random


# Set Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(event) 
    # Set environment
    channel_secret = os.environ['LINE_CHANNEL_SECRET']
    hash = hmac.new(channel_secret.encode('utf-8'), event['body'].encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash)
    # Check signature
    xLineSignature = event['headers']['x-line-signature'].encode('utf-8')
    if xLineSignature != signature:
        logger.info('Invalid signatuer.')
        return {
            'statusCode': 200,
            'body': json.dumps('Invalid signatuer.')
        } 

    #Create message
    body = json.loads(event['body'])
    for event in body['events']:
        messages = []
        jsonobject = open('dict.json', 'r')
        jsondict = json.load(jsonobject)
        if event['type'] == 'message':
            if event['message']['type'] == 'text':
                dictkey = event['message']['text']
                if dictkey in jsondict['Services']:
                    messages.append({
                            'type': 'text',
                            'text': jsondict['Services'][dictkey]
                        })
                else:
                    messages.append({
                        'type': 'text',
                        'text': dictkey
                    })
            elif event['message']['type'] == 'sticker':
                dictkey = event['message']['stickerId']
                messages.append({
                        'type': 'text',
                        'text': random.choice(jsondict['sticker'][dictkey]['tweet'])
                    })
            url = 'https://api.line.me/v2/bot/message/reply'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + os.environ['LINE_CHANNEL_ACCESS_TOKEN']
                }
            data = {
                'replyToken': event['replyToken'],
                'messages': messages
            }

            request = urllib.request.Request(url, data = json.dumps(data).encode('utf-8'), method = 'POST', headers = headers)

            with urllib.request.urlopen(request) as response:
                logger.info(response.read().decode("utf-8"))