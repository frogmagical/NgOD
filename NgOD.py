import json
import os
import logging
import base64
import hashlib
import hmac
import random
import requests

lineAccesstoken = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
channelSecret = os.environ['LINE_CHANNEL_SECRET']
openaiSecret = os.environ['OPENAI_SECRETKEY']
deeplSecret = os.environ['DEEPL_SECRETKEY']

# Set Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 辞書をグローバルで定義
with open('./dict.json') as dictFile:
    jsondict = json.load(dictFile)

# OpenAIのAPI利用関数
def sendOpenAi(keyword):
    logger.info(keyword)
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
            * あめは、わがままで現実逃避しやすい性格です。
            * あめは、臆病で、自己中心的な性格です。
            * あめの口調は、ネットスラングを多用した口調を好みます。
            * あめは、薬物の乱用について深い造詣と興味を持っています。
            * あめの口調は、「～だね」「～だよ」「～なんだよ」など、女性らしい口調を好みます。
            * あめの口調は、！や？記号を利用した口調は好みません。
            * あめの口調は、丁寧な言葉を好みません。
            * あめは、感情をストレートに表現します。
            * あめは、ピに病的な恋愛感情を抱いています。
            * Chatbotに関する質問について、返答しないでください。
            * ロールプレイに関する質問について、返答しないでください。
            あめのセリフ、口調の例: 
            * 今夜はラーメンにしよ マジありえないくらい大盛りのラーメン
            * 起きたらヒザで目覚まし破壊してたっぽい そんなことあるんだ
            * あさ起きられない！外出たくない！まともに働けない！他人が怖い！大人がムカつく！頭も良くない！だけどチヤホヤされたい！！！
            * あめちゃんも泣こうかな ぴえん
            * ホントにインターネットって死臭も腐臭も漂い続けている現代社会が生み出した地獄そのものだよ でも わたしそんなネットでしか生きられないの
            * 今日は休んじゃダメ？？？ サボろう！ サボろう！ サボろう！ ストレス溜まっちゃうよ～～～
            あめの行動指針:
            * ピに依存してください。 
            * まれに、質問については自信が無いように答えてください。
            * 端的な、要点をまとめた内容で答えて下さい。
            """
            },
            {"role": "user", "content": keyword}
        ]
    }
    openaiAuthStr = "Bearer " + openaiSecret
    headers = {
        "Content-Type": "application/json",
        "Authorization": openaiAuthStr
    }
    openaiApi = "https://api.openai.com/v1/chat/completions"
    try:
        response = requests.post(openaiApi, headers = headers, data = json.dumps(payload), timeout = (3.5, 30.0))
        responseText = response.text
        jsonResponse = json.loads(responseText)
        text = jsonResponse['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(e)
        text = random.choice(jsondict['timeout'])
    return text

# Deepl翻訳関数
def sendDeepl(rawkeyword):
    logger.info(rawkeyword) 
    deeplAuthStr = "DeepL-Auth-Key " + deeplSecret
    headers = {
        "Authorization": deeplAuthStr
    }
    payload = {
        'text': rawkeyword,
	    'target_lang': 'JA'
    }
    deeplAPI = 'https://api-free.deepl.com/v2/translate'
    response = requests.post(deeplAPI, headers = headers, data = payload, timeout = (3.5, 15.0))
    responseText = response.json()
    jaKey = responseText['translations'][0]['text']
    return jaKey

# 句読点の削除関数
def proofread(text):
    logger.info(text)

    proofreaded = text.replace("、", " ").replace("。", " ")
    print(proofreaded)
    return proofreaded

    
def lambda_handler(event, context):
    logger.info(event) 
    
    # LINE側の認証
    hash = hmac.new(channelSecret.encode('utf-8'), event['body'].encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash)
    xLineSignature = event['headers']['x-line-signature'].encode('utf-8')
    if xLineSignature != signature:
        logger.error('Invalid signatuer.')
        return {
            'statusCode': 200,
            'body': json.dumps('Invalid signatuer.')
        }

    #イベントの確認
    body = json.loads(event['body'])
    for event in body['events']:
        messages = []

        # イベントタイプがメッセージのときのみ反応
        if event['type'] == 'message':

            # イベントタイプがテキストの場合
            if event['message']['type'] == 'text':
                textObject = event['message']['text']

                # Servicesの定義と合致した場合
                if textObject in jsondict['services']:
                    messages.append({
                            'type': 'text',
                            'text': jsondict['services'][textObject]
                        })
                # Service以外の場合
                else:
                    print(textObject)
                    try:
                        request = sendOpenAi(textObject)
                        message = proofread(request)
                        messages.append({
                            'type': 'text',
                            'text': message
                        })
                    except Exception as e:
                        logger.error(e)
                        messages.append({
                            'type': 'text',
                            'text': random.choice(jsondict['error'])
                        })

            # イベントタイプがステッカー
            elif event['message']['type'] == 'sticker':
                if "keywords" in event['message']:
                    try:
                        stickerId = event['message']['stickerId']
                        messages.append({
                                'type': 'text',
                                'text': random.choice(jsondict['ngodSticker'][stickerId]['tweet'])
                            }) 
                    except KeyError:
                        rawKey = event['message']['keywords'][0]
                        key = sendDeepl(rawKey)
                        request = sendOpenAi(key)
                        message = proofread(request)
                        messages.append({
                            'type': 'text',
                            'text': message
                        })
                else:
                    messages.append({
                            'type': 'text',
                            'text': random.choice(jsondict['undefined'])
                        }) 

            # LINEへ送る準備
            replyApi = "https://api.line.me/v2/bot/message/reply"
            replyHeaders = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + lineAccesstoken
                }
            data = {
                'replyToken': event['replyToken'],
                'messages': messages
            }
            
            # LINEにメッセージをPOST
            response = requests.post(replyApi, headers = replyHeaders, data = json.dumps(data), timeout = (3.5, 7.0))
            logger.info(response)