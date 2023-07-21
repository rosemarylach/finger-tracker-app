import pandas as pd
import matplotlib.pyplot as plt
 
# take data
data = pd.read_csv("output5.csv", names=["x", "y"])
 
# form dataframe
# print(data)
 
# plot the dataframe
data.plot(x="x", y="y", kind="scatter", figsize=(9, 8))
 
# print bar graph
plt.show()