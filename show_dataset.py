import pandas as pd
from pandasgui import show
dt = pd.read_csv("data/data2.csv")
show(dt)
print(dt.head())
