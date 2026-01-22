import pandas as pd

df = pd.read_excel("sample_data/angajati.xlsx")
print(df[["CNP"]].head(10))
print(df["CNP"].head(10).apply(lambda x: (x, type(x), str(x))).tolist())
