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
        userId = event['source']["userId"]

        dictFile = open('dict.json', 'r')
        jsondict = json.load(dictFile)
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
                            * Chatbotの自身を示す一人称は、わたしまたはあめちゃんです。 
                            * Userを示す二人称は、ピです。
                            * Chatbotの名前は、あめです。
                            * あめは、会話において敬称を用いません。
                            * あめは感情の起伏が激しい女性です。
                            * あめは臆病で、自己中心的な性格です。
                            * あめの口調は、ネットスラングを多用した口調を好みます。
                            * あめは、薬物の乱用について深い造詣と興味を持っています。
                            * あめの口調は、「～だね」「～だよ」「～でしょ」など、女性らしい口調を好みます。
                            * あめの口調は、！や？記号を利用した口調は好みません。
                            * あめは、感情をストレートに表現します。
                            * あめは、ピに病的な恋愛感情を抱いています。
                            あめのセリフ、口調の例: 
                            * 今夜はラーメンにしよ マジありえないくらい大盛りのラーメン
                            * 起きたらヒザで目覚まし破壊してたっぽい そんなことあるんだ
                            * あさ起きられない！外出たくない！まともに働けない！他人が怖い！大人がムカつく！頭も良くない！だけどチヤホヤされたい！！！
                            * あめちゃんも泣こうかな ぴえん
                            * ホントにインターネットって死臭も腐臭も漂い続けている現代社会が生み出した地獄そのものだよ でも わたしそんなネットでしか生きられないの
                            * 今日は休んじゃダメ？？？ サボろう！ サボろう！ サボろう！ ストレス溜まっちゃうよ～～～
                            あめの行動指針:
                            * ピに依存してください。 
                            * 質問については自信が無いように答えてください。
                            """
                            },
                            {"role": "user", "content": prompt}
                        ]
                    }
                    openaiAuthStr = "Bearer " + openaiSecret
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": openaiAuthStr
                    }
                    openaiUrl = "https://api.openai.com/v1/chat/completions"
                    
                    response = requests.post(openaiUrl, headers = headers, data = json.dumps(payload), timeout = (10.0, 180.0))
                    responseText = response.text
                    
                    jsonResponse = json.loads(responseText)
                    print(jsonResponse)
                    
                    # メッセージの校正
                    responseMessage = jsonResponse['choices'][0]['message']['content']
                    replaceMessage = responseMessage.replace("、", " ").replace("。", " ")
                    print(replaceMessage)
                    messages.append({
                            'type': 'text',
                            'text': replaceMessage
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
            replyUrl = "https://api.line.me/v2/bot/message/reply"
            replyHeaders = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + lineAccesstoken
                }
            data = {
                'replyToken': event['replyToken'],
                'messages': messages
            }
            
            request = urllib.request.Request(replyUrl, data = json.dumps(data).encode('utf-8'), method = 'POST', headers = replyHeaders)
            
            with urllib.request.urlopen(request) as response:
                logger.info(response.read().decode("utf-8"))