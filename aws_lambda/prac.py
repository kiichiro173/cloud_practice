import pandas as pd

data = pd.read_csv("/Users/kiichiro/Desktop/download_data/Customer_Master.csv" ,header=0 ,encoding="shift_jis")

print(data.head())
print("5行目を取得する")
print(data.iloc[:,0:3])
