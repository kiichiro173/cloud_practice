import datetime
import os

import airflow
from airflow.contrib.operators import bigquery_operator, \
    bigquery_table_delete_operator, gcs_to_bq
import pendulum

# DAGの共通のパラメータの定義

default_args ={
    "owner": "gcpbook",
    "depends_on_past":False,
    "email":[""],
    "email_on_failure":False,
    "email_on_retry":False,
    "retries":1,
    "retry_delay": datetime.timedelta(minutes=5),
    "start_date": pendulum.today("Asia/Tokyo").add(hours=2)
}
# retriesを１にすると、実行がうまくいかなかった場合一度だけ再実行される。
# retry_delayはタスクが失敗してから5分後にリトライ処理が開始される。
# start_date:DAGの作成時の午前2時が開始日時となる。


# DAGの定義を行う。
with airflow.DAG(
    "count_users",
    default_args=default_args,
    # 日時でDAGの実行を行う。
    schedule_interval=datetime.timedelta(days=1),
    catchup=False
) as dag:
    # count_usersというIDを付与
    # schedule_intervalにおいてDAGが日時で実行されるようにする。
    # catchup=False によって過去の日付の処理は実行しないようにしている。

    """
    各タスクの概要に関して
    load_events:gcsのデータをBigqueryの作業用テーブルに取り込む
    insert_dau:作業用テーブルとユーザ情報テーブルの結合。そのあとに分析結果をgcpbook_ch5.dauテーブルに書き込み
    delete_work_table:BigQueryの作業テーブルを削除する
    """
    load_events = gcs_to_bq.GoogleCloudStorageToBigQueryOperator(
        task_id='load_events',
        bucket=os.environ.get('PROJECT_ID') + '-gcpbook-ch5',
        source_objects=['data/events/{{ ds_nodash }}/*.json.gz'],
        destination_project_dataset_table='gcpbook_ch5.work_events',
        source_format='NEWLINE_DELIMITED_JSON'
    )
    # buket:環境変数でPROJECT_IDを作成したのでそれを使用している。
    # source_objectsのds_nodashはjinjaテンプレートで使用しているもの(実行日を指している。https://qiita.com/birdmoor23/items/4772e6943ff54088ef5e)
    # destination_project_dataset_tableここのテーブルにデータがロードされる。
    # source_formatロード対象のデータファイルの形式を指定している。

    insert_dau = bigquery_operator.BigQueryOperator(
        task_id='insert_dau',
        use_legacy_sql=False,
        sql="""
            insert gcpbook_ch5.dau
            select
                date('{{ ds }}') as dt
            ,   countif(u.is_paid_user) as paid_users
            ,   countif(not u.is_paid_user) as free_to_play_users
            from
                (
                    select distinct
                        user_pseudo_id
                    from
                        gcpbook_ch5.work_events
                ) e
                    inner join
                        gcpbook_ch5.users u
                    on
                        u.user_pseudo_id = e.user_pseudo_id
        """
    )
    # use_legacy_sql=FalseにすることによってBigqueryの標準SQLが使用される。


    delete_work_table = \
        bigquery_table_delete_operator.BigQueryTableDeleteOperator(
            task_id='delete_work_table',
            deletion_dataset_table='gcpbook_ch5.work_events'
        )
    # 実行時にこのBigQueryのデータセットgcpbook_ch5のwork_eventsが削除される。
    


    # 各タスクの依存関係を定義する。
    load_events >> insert_dau >> delete_work_table