"""
    cloud_functionを使用してデータの処理を行っていく。
    GCSにアップされたデータをCloudFunctionでBigqueryにインサートする。
    
    参考資料：
    https://qiita.com/komiya_____/items/8fd900006bbb2ebeb8b8
    https://hayaengineer.com/%E3%82%AF%E3%83%A9%E3%82%A6%E3%83%89%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/gcp/bigquery/%E3%80%90%E3%82%B5%E3%83%B3%E3%83%97%E3%83%AB%E3%82%B3%E3%83%BC%E3%83%89%E3%81%82%E3%82%8A%E3%80%91bigquery%E3%81%ABpython%E3%81%AEpandas%E3%81%A7%E6%9B%B8%E3%81%8D%E8%BE%BC%E3%81%BF%E3%83%BB%E8%AA%AD/
"""
import pandas as pd
from io import BytesIO
from google.cloud import storage


def my_first_func(event, context):
    bucket_name:str = event['bucket']
    file_name:str = event['name']
    file_type:str = event['contentType']


    if file_name.split("/")[0] != "inami1":
        print(f"このファイルは処理を行いたいフォルダではないため処理を中断いたします。file_name: {file_name} , buket_name: {bucket_name}")
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
    bucket_name = "upload_inami"
    bucket = storage_client.get_bucket(bucket_name)
    new_file_name = "upload_inami/part2.csv"
    blob = storage.Blob(new_file_name, bucket)
    blob.upload_from_string(
        data=df_csv.to_csv(index=False),
        content_type="text/csv")
    print("データのアップロードが無事に終了いたしました。")
    
    # Bigqueryに書き込み
    try:
        project_id = "プロジェクトID"
        table_id  = "dataset_name.table_name"
        df_csv.to_gbq(table_id,project_id)
        print("Bigqueryへアップロード完了しました。")
    except:
        print("Bigqueryへの取り込みに失敗いたしました。")