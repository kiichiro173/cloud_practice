# エンコーディングが必要なデータをエンコーディングしてからBigqueryに入れるスクリプト

import pandas as pd

file_path = '/Users/kiichiro/Desktop/data/cloud_practice/gcp_prac/Customer_Master.csv'

df = pd.read_csv(file_path, encoding='shift-jis')
print(df)

dataset_id = 'kittyomo'
table_id = 'customer2'

# カラム名を英語表記に修正
df = df.rename(columns={"顧客 Id":"customer_id","名前":"name","性別":"sex","年齢":"age","誕生日":"birth_day","婚姻":"married_flag","血液型":"blood","都道府県":"prefecture","キャリア":"career","カレーの食べ方":"eating"})
print(df.head())
df.to_gbq('{}.{}'.format(dataset_id, table_id), if_exists='replace')