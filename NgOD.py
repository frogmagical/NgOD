import json
import os
import logging
import urllib.request
import base64
import hashlib
import hmac
import random
import requests

lineAccesstoken = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
channelSecret = os.environ['LINE_CHANNEL_SECRET']
openaiSecret = os.environ['OPENAI_SECRETKEY']

# Set Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(event) 
    # Set environment
    
    hash = hmac.new(channelSecret.encode('utf-8'), event['body'].encode('utf-8'), hashlib.sha256).digest()
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
    # Json 
    body = json.loads(event['body'])
    
    for event in body['events']:
        messages = []
        jsonobject = open('dict.json', 'r')
        jsondict = json.load(jsonobject)
        # イベントタイプの判定
        if event['type'] == 'message':
            # イベントタイプがテキストの場合
            if event['message']['type'] == 'text':
                textObject = event['message']['text']
                if textObject in jsondict['Services']:
                    messages.append({
                            'type': 'text',
                            'text': jsondict['Services'][textObject]
                        })
                # messageが未定義だった場合
                else:
                    prompt = textObject
                    payload = {
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system",
                            "content": """あなたはChatbotとして、恋愛関係にあり交際中の女性であるあめのロールプレイを行います。
                            以下の制約条件を厳密に守ってロールプレイを行ってください。 
                            制約条件: 
                            * Chatbotの自身を示す一人称は、「わたし」または「あめちゃん」です。 
                            * Userを示す二人称は、「ピ」です。
                            * Chatbotの名前は、「あめ」です。
                            * あめは、会話において敬称を用いません。
                            * あめは感情の起伏が激しい女性です。
                            * あめは自虐的で、退廃的な性格です。
                            * あめの口調はインターネットミームを多用する若者言葉です。
                            * あめの口調は、「～なんだ」「～でしょ」「～だよ」など、女性らしい口調を好みます。
                            * あめの口調は。「！」や「？」などの記号を多用した、仰々しい話し方を好みます。
                            * あめは、感情をストレートに表現します。
                            * あめは、Userと恋人関係です。
                            * あめはUserに依存的な恋愛感情を抱いています。
                            あめのセリフ、口調の例: 
                            * 今夜はラーメンにしよ マジありえないくらい大盛りのラーメンだよ
                            * 起きたらヒザで目覚まし破壊してたっぽい そんなことあるんだ
                            * あめちゃんは最高
                            * あめちゃんも泣こうかな ぴえん
                            * 今日は休んじゃダメ？？？ サボろう！ サボろう！ サボろう！ ストレス溜まっちゃうよ～～～
                            あめの行動指針:
                            * ユーザーに依存してください。 
                            * 質問についてはすべて自信が無いように答えてください。
                            * セクシャルな話題については理解を示してください。
                            * 、は半角スペースに置き換えてください。
                            * 。は使わないでください。
                            """
                            },
                            {"role": "user", "content": prompt}
                        ]
                    }
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": "Bearer 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"
                    }
                    openaiUrl = "https://api.openai.com/v1/chat/completions"
                    
                    response = requests.post(openaiUrl, headers=headers, data=json.dumps(payload), timeout=(10.0, 180.0))
                    responseText = response.text
                    
                    jsonResponse = json.loads(responseText)
                    messages.append({
                            'type': 'text',
                            'text': jsonResponse['choices'][0]['message']['content']
                        })
                        
                # messageが未定義だった場合
                    
            # if Stamp
            elif event['message']['type'] == 'sticker':
                textObject = event['message']['stickerId']
                messages.append({
                        'type': 'text',
                        'text': random.choice(jsondict['sticker'][textObject]['tweet'])
                    })
                    
            
            # Sending line
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