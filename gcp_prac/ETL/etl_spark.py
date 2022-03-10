"""
    Sparkに関して
    →https://qiita.com/miyamotok0105/items/bf3638607ef6cb95f01b
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count , lit , to_date , when

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket",dest="buket" , help="Cloud Storage bucket")
    parser.add_argument("--dt",dest="dt",help="event date")
    args = parser.parse_args()


    spark = SparkSession.builder.appName('CountUsers').getOrCreate()
    # BigQueryのテーブルへのロード時に使用されるCloud Storageのバケットを設定する。
    spark.conf.set('temporaryGcsBucket', args.bucket)

    # ファイル読み取り対象のCloud Storageのパスを組み立てる。
    event_file_path = 'gs://{}/data/events/{}/*.json.gz'\
        .format(args.bucket, args.dt)
    # 処理対象のイベント日付を"YYYY-MM-DD"形式で組み立てる。
    dt = '{}-{}-{}'.format(args.dt[0:4], args.dt[4:6], args.dt[6:8])

    # Cloud Storageからユーザ行動ログを読み取り、user_pseudo_idの一覧を抽出する。
    user_pseudo_ids = spark.read.json(event_file_path)\
        .select('user_pseudo_id').distinct()

    # BigQueryのユーザ情報を保管するテーブルgcpbook_ch5.usersからデータを読み取る。
    users = spark.read.format('bigquery').load('gcpbook_ch5.users')

    # 前工程で抽出したuser_pseudo_idsとusersを結合し、集計して、
    # 課金ユーザと無課金ユーザそれぞれの人数を算出し、その結果をBigQueryの
    # テーブルgcpbook_ch5.dauへ書き込む。
    user_pseudo_ids.join(users, 'user_pseudo_id') \
        # 集計
        .agg(count(when(col('is_paid_user'), 1)).alias('paid_users'),count(when(~col('is_paid_user'), 1)).alias('free_to_play_users'))\
        # 日付のカラムを新しく追加:https://data-analysis-stats.jp/spark/pyspark%E3%81%A7dataframe%E3%81%AB%E5%88%97%E3%82%92%E8%BF%BD%E5%8A%A0%E3%81%99%E3%82%8B%E6%96%B9%E6%B3%95/
        .withColumn('dt', to_date(lit(dt)))\
        .select('dt', 'paid_users', 'free_to_play_users')\
        .write.format('bigquery').option('table', 'gcpbook_ch5.dau')\
        .mode('append').save()

    # SparkSessionに紐づくSparkContextを停止させる。
    spark.stop()


if __name__ == "__main__":
    run()