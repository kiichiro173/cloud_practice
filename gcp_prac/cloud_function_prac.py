"""
    cloud_functionを使用してデータの処理を行っていく。
    ドキュメント: https://cloud.google.com/functions/docs/tutorials/storage#object_finalize
    参考文献：https://dev.classmethod.jp/articles/cloud-functions-gcs-trigger-load-data2bigquery/
    自分で作成した関数を呼び出したい時はエントリーポイントを修正すると使用する事ができるようになる！！


実行内容に関して
GCSにアップロードされたデータを加工して指定のGCSにアップロードを行う。
→バケットの一部のフォルダは加工するけど一部のファイルは加工しないというような関数を作成する。

GCSの操作に関して
→https://qiita.com/kenkanayama/items/1050e8a10f23d5efbbd8
→https://dev.classmethod.jp/articles/cloud-functions-gcs-trigger-load-data2bigquery/

GCSのデータのアップロードとダウンロードに関して
→https://dodotechno.com/python-gcs/

requirements.txtを作成するのを忘れずに！
→https://qiita.com/k_shim/items/a548453a2fb6a42d4058#requirementstxt%E3%81%AE%E4%BD%9C%E6%88%90
"""
import pandas as pd
from io import BytesIO
from google.cloud import storage


def my_first_func(event, context):
    bucket_name:str = event['bucket']
    file_name:str = event['name']
    file_type:str = event['contentType']


    if file_name.split("/")[0] != "inami1":
        print("このファイルは処理を行いたいフォルダではないため処理を中断いたします。file_name: {file_name} , buket_name: {bucket_name}")
        return

    if "csv" not in file_type :
        print(f"これはcsvファイルではないため、処理を中断いたします。file_name: {file_name} , buket_name: {bucket_name}")
        return

    # データの読み込み！
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = storage.Blob(file_name, bucket)
    content = blob.download_as_string()
    df_csv = pd.read_csv(BytesIO(content))

    print("データの取得が完了いたしました。")
    print(df_csv.head())

    # 新しいカラムを追加
    df_csv["inami"] = "inami"


    # データのアップロード
    bucket = storage_client.get_bucket(bucket_name)
    new_file_name = "upload_inami/part2.csv"
    blob = storage.Blob(new_file_name, bucket)
    blob.upload_from_string(
        data=df_csv.to_csv(index=False),
        content_type="text/csv")
    print("データのアップロードが無事に終了いたしました。")