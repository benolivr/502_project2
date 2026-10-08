import geopandas as gpd
import pandas as pd

from libpysal import weights
import seaborn as sns
import numpy as np
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt

data=gpd.read_file("public_highschools_clean.geojson")

data["nearest_larger"]=None
data["distance_to_nearest"]=None

for i in data.index:
    current=data.loc[i]
    bigger=data[data["ccd_enroll_2023"]>current["ccd_enroll_2023"]]

    if len(bigger) == 0:
        continue
    distances= bigger.geometry.distance(current.geometry)
    closest =distances.idxmin()
    data.loc[i,"nearest_larger"]=data.loc[closest,"SCHOOL_NAME"]
    data.loc[i,"distance_to_nearest"]=distances[closest]/1000

data["region"]=data["longitude"].apply(lambda x: "West" if x < -110 else "East")

pd.set_option('display.max_rows', 1000)
print(data.columns)

fig, ax= plt.subplots(figsize=(9,6))
ax=sns.scatterplot(data=data, x="pct_change_10yr", y="distance_to_nearest",hue="region", size="ccd_enroll_2023", sizes=(20,400), size_norm=LogNorm(), alpha=0.6, ax=ax)
ax.set_yscale('log')
ax.axvline(0, color="gray", linestyle="--", linewidth=1) 
ax.axhline(30,color="gray",linestyle="--", linewidth=1)
ax.set_xlabel("Enrollment change, 2013-2023 (%)")
ax.set_ylabel("Distance to nearest larger school (log scale)")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")      

ax.annotate(
    data.iloc[156]["SCHOOL_NAME"],
    xy=(data.iloc[156]["pct_change_10yr"], data.iloc[156]["distance_to_nearest"]),
    xytext=(8, 8),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="-", color="gray"),
)

ax.annotate(
    data.iloc[160]["SCHOOL_NAME"],
    xy=(data.iloc[160]["pct_change_10yr"], data.iloc[160]["distance_to_nearest"]),
    xytext=(8, 8),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="-", color="gray"),
)

ax.annotate(
    data.iloc[131]["SCHOOL_NAME"],
    xy=(data.iloc[131]["pct_change_10yr"], data.iloc[131]["distance_to_nearest"]),
    xytext=(8, 8),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="-", color="gray"),
)

plt.tight_layout()
plt.show()


print(data.sort_values("distance_to_nearest", ascending=False))