import apache_beam as beam
import os
    """
    単純にhogeを付け加えるといった処理を行なっている。
    →これを実行するとライン一つ一つにhogeを付け加えるといった処理を行なっている。
    """

def run_pipeline():
    with beam.Pipeline('DirectRunner') as pipeline:

        # [Final Output PCollection] = ([Initial Input PCollection]
        #                               | [First Transform]
        #                               | [Second Transform]
        #                               | [Third Transform])
        input_data = (pipeline
        | 'read_file' >> beam.io.ReadFromText('./sample.txt')
        | 'add_hoge_string' >> beam.Map(lambda line: line + "hoge")
        )

        # input_dataの内容をファイルに書き出す
        input_data | beam.io.WriteToText('./data/output.txt')


if __name__ == '__main__':
    # working directoryを実行ファイルのある場所に変更
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_pipeline()