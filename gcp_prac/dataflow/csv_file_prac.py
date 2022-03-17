import apache_beam as beam
import os

"""
データにaがあるかどうかで異なる処理を行うように修正
"""


class AppendStringEachline(beam.DoFn):

    def process(self, element):
        print("elementの確認")
        print(element)
        print()
        yield element


def run_pipeline():
    with beam.Pipeline('DirectRunner') as pipeline:

        # from past.builtins import unicode
        input_data = (
                pipeline
                # sample.txtを読み込んで
                | 'read_file' >> beam.io.textio.ReadFromText('./hacker2_data.csv')
                # 各行の最後に "hoge" を追加する
                # | 'add_hoge_string' >> beam.transforms.core.Map(lambda line : line + "hoge") # つまり左記と同じ結果
                | 'add_hoge_string' >> (beam.transforms.core.ParDo(AppendStringEachline()).with_output_types(str))
                # .with_output_types(unicode) について:
                # apache_beam.typehints.decorators.with_output_types(*return_type_hint, **kwargs)
                # https://beam.apache.org/releases/pydoc/2.21.0/apache_beam.typehints.decorators.html#apache_beam.typehints.decorators.with_output_types
                # 返り値の型をアノテーションしている。なくても動くけどあったほうが親切。
                # from past.builtins import unicode
        )

        # input_dataの内容をファイルに書き出す
        input_data | beam.io.textio.WriteToText('./data/output_csvfile.txt')


if __name__ == '__main__':
    # working directoryを実行ファイルのある場所に変更
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_pipeline()