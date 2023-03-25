# あめちゃんを召喚するLINEBOT

## 前提
- バックエンドはGCPではなくてAWS Lambdaを利用します。
- 下手の横好きで書いたコードなので可読性悪いしきれいなコードじゃないです。
- 別途以下のサービスのAPIを利用します。
    - LINE Developers Messaging API
    - OpenAI API
    - Deepl API

## 構成
[LINE] ←→ [LINEAPI] ←→ [Lambda]

## Lambdaでやってること
[Deepl] → [OpenAI] → [LINEAPI]

## 注意点
- APIキーとかはLambdaの環境変数にぶち込んで下さい
- ChatGPTに与える人格プロンプト部分は好きに変えて遊べますたぶん