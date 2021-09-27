import pandas as pd

pd.set_option('display.max_columns', None)
df = pd.read_csv('zest_data.csv', delimiter='|', header=0)
print(df)
