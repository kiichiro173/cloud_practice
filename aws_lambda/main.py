"""
参考資料

→https://dev.classmethod.jp/articles/lambda-my-first-step/
→https://tech.bita.jp/article/38
→https://www.youtube.com/watch?v=BDviXnpOCms
→https://www.youtube.com/watch?v=36lVbVHeIXE
→https://www.youtube.com/watch?v=JNzOTwRsIoQ
"""

import io
import boto3
import pandas as pd


def handler(event, context):
    try:
        # 必要な定数を定義
        BUKET_NAME = event['Records'][0]['s3']['bucket']['name']
        BUKET_KEY = event['Records'][0]['s3']['object']['key']
        UPLOAD_BUKET_KEY = "new_csv.csv"
        print("バケット名とバケットキーを取得しました！！")
        print(f"BUKET_NAME: {BUKET_NAME}")
        print(f"BUKET_KEY: {BUKET_KEY}")
        # pandasでcsvファイルを取得してくる。
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=BUKET_NAME, Key=BUKET_KEY)
        data = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='shift_jis')
    
        print("dataの中身を確認")
        print(data.head())
    
        # 修正したデータのuploadを行う。
        new_data = data.iloc[:,0:3]
    
        # データの保存
        # 保存領域を準備
        buf = io.BytesIO()
    
        # メモリに保存
        new_data.to_csv(buf)
    
        # バイトデータをアップロード
        res = s3.put_object(
            Bucket=BUKET_NAME, 
            Key=UPLOAD_BUKET_KEY, 
            Body=buf.getvalue()
        )
        
        if res["ResponseMetadata"]["HTTPStatusCode"] == 200:
            print(f"[SUCCESS] upload {UPLOAD_BUKET_KEY}")
    except:
        print(f"予期せぬエラーが発生しました。確認をお願いいたします！！buket_name:{BUKET_NAME} , buket_key:{BUKET_KEY}")