# 必要モジュールのインストール
import argparse
import json
import logging

import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions

# 書き込み先のBigqueryテーブルのdauテーブルのスキーマを定義する。
_DAU_TABLE_SCHEMA = {
    'fields': [
        {"name":"dt","type":"date","mode":"required"},
        {"name":"paid_users","type":"int64","mode":"required"},
        {"name":"free_to_play_users","type":"int64","mode":"required"}
               ]
}

# 変換処理(Combine Transform)で使用されるクラスを定義する。
# 今回はCountUsersFnとした。

class CountUsersFn(beam.CombineFn):
    # 課金ユーザーと無課金ユーザの人数を集計する。
    # CombineFnの関数は大きく四つの構成に別れている。
    # https://beam.apache.org/documentation/programming-guide/#combine

    def create_accumulator(self) -> int:
        """
        課金ユーザと無課金ユーザの人数を保持するaccumulatorを作成して返却する。
        Returns:
            (int , int)
            課金ユーザと無課金ユーザの人数を表すタプル
        """
        return 0,0

    def add_input(self, accumulator, is_paid_user):
        """
        課金ユーザと無課金ユーザの人数を加算
        Args:
            accumulator (_type_):  課金ユーザと無課金ユーザの人数を表すタプル
            is_paid_user (bool): 課金ユーザであるか否かを表すフラグ

        Returns:
                加算後の課金ユーザーと無課金ユーザの人数を表すタプル
        """
        (paid , free) = accumulator
        if is_paid_user:
            return paid + 1 , free
        else:
            return paid , free + 1

    def merge_accumulators(self,accumulators):
        """複数のaccumulatorを単一のaccumulatorにマージした結果を返す

        Args:
            accumulators (_type_): マージ対象の複数のaccumulators
        Returns:
            マージ後のaccumulator
        """
        paid , free = zip(*accumulators)
        return sum(paid) , sum(free)

    def extract_output(self,accumulator):
        """集計後の課金ユーザーと無課金ユーザを返却する。

        Args:
            accumulator (_type_): 課金ユーザと無課金ユーザを返却する
        Returns:
            集計後の課金ユーザと無課金ユーザの人数を表すタプル
        """
        return accumulator

def run():
    ## コマンドラインの引数を定義する。
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dt",
        dest="dt",
        help="event date"
    )
    # known_argsは既知の引数とまだ知らない引数を返す事ができる。
    # →https://rcmdnk.com/blog/2014/12/25/computer-python/
    known_args, pipeline_args = parser.parse_known_args()

    pipeline_options = PipelineOptions(pipeline_args)

    #ファイル読み取り対象のCloud Strageのパスを組み立てる。
    event_file_path = 'gs://{}-gcpbook-ch5/data/events/{}/*.json.gz'.format(
        pipeline_options.view_as(GoogleCloudOptions).project, known_args.dt)
    # 処理対象のイベント日付を"YYYY-MM-DD"形式で組み立てる
    dt ='{}-{}-{}'.format(known_args.dt[0:4],known_args.dt[4:6],known_args.dt[6:8])

    with beam.Pipeline(options=pipeline_options) as p:
        # cloud Storageからユーザ行動ログを読み取り、user_pseudo_idの一覧を抽出する。
        user_pseudo_ids =(
            p
            # Cloud Storageからデータを読み取る
            | "Read Events" >> ReadFromText(event_file_path)
            # json形式のデータをパースしてuser_pseudo_idを抽出する
            | "Parse Events" >> beam.Map(
                lambda event: json.loads(event).get('user_pseudo_id')
            )
            # 重複しているuser_pseudo_idを排除する。
            | 'Deduplicate User Pseudo Ids' >> beam.Distinct()
            # 後続の結合処理で必要となるため、キー・バリュー形式にデータを変換する。
            # user_pseudo_idをキーとし、値は使用しないためNoneとする。
            | 'Transform to KV' >> beam.Map(
                lambda user_pseudo_id: (user_pseudo_id, None)
            )
        )
        # BigQueryのユーザ情報を保管するテーブルgcpbook_ch5.usersからユーザ情報の
        # 一覧を取得する。
        users = (
            p
            # BigQueryのユーザ情報を保管するテーブルgcpbook_ch5.usersからデータを読み取る。
            | 'Read Users' >> beam.io.Read(
                beam.io.BigQuerySource('gcpbook_ch5.users'))
            # 後続の結合処理で必要となるため、キー・バリュー形式にデータを変換する。
            # user_pseudo_idをキーとし、「課金ユーザであるか否か」を表すis_paid_userを値とする。
            | 'Transform Users' >> beam.Map(
                lambda user: (user['user_pseudo_id'], user['is_paid_user']))
        )
        # 前工程で作成した2つのPCollection user_pseudo_idsとusersを結合し、
        # 集計して、課金ユーザと無課金ユーザそれぞれの人数を算出して、その結果をBigQueryのテーブルgcpbook_ch5.dauへ書き込む。
        (
            {'user_pseudo_ids': user_pseudo_ids, 'users': users}
            # user_pseudo_idsとusersを結合する。
            | 'Join' >> beam.CoGroupByKey()
            # ユーザ行動ログが存在するユーザ情報のみを抽出する。
            | 'Filter Users with Events' >> beam.Filter(
                lambda row: len(row[1]['user_pseudo_ids']) > 0)
            # 「課金ユーザであるか否か」を表すフラグ値を抽出する。
            | 'Transform to Is Paid User' >> beam.Map(
                lambda row: row[1]['users'][0])
            # 課金ユーザと無課金ユーザそれぞれの人数を算出する。
            | 'Count Users' >> beam.CombineGlobally(CountUsersFn())
            # BigQueryのテーブルへ書き込むためのデータを組み立てる。
            | 'Create a Row to BigQuery' >> beam.Map(
                lambda user_nums: {
                    'dt': dt,
                    'paid_users': user_nums[0],
                    'free_to_play_users': user_nums[1]
                })
            # BigQueryのテーブルgcpbook_ch5.dauへ算出結果を書き込む。
            | 'Write a Row to BigQuery' >> beam.io.WriteToBigQuery(
                'gcpbook_ch5.dau',
                schema=_DAU_TABLE_SCHEMA,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED)
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()