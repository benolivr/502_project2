import geopandas as gpd
import matplotlib.pyplot as plt
from pysal.lib import weights 
import seaborn as sns 
import pandas as pd
from scipy.spatial import ckdtree

data=gpd.read_file("public_highschools_with_ccd.geojson")
secondary=gpd.read_file("MontanaSchoolDistricts_shp/MontanaSchoolDistricts_shp/Secondary.shp")
unified=gpd.read_file("MontanaSchoolDistricts_shp/MontanaSchoolDistricts_shp/Unified.shp")

w=weights.KNN.from_dataframe(data, k=1)

# w = weights.KNN.from_dataframe(data, k=1)   (data already projected to meters)

# position of each school's nearest neighbor
nn_pos = [w.neighbors[i][0] for i in range(len(data))]

# distance from each school to its neighbor, in km
data["nn_dist_km"] = data.geometry.distance(data.geometry.iloc[nn_pos], align=False) / 1000

# map
ax = data.plot(column="nn_dist_km", cmap="viridis", legend=True,
               legend_kwds={"label": "Distance to nearest school (km)"},
               markersize=20, figsize=(10, 6))
ax.set_axis_off()
plt.show()

# histogram
data["nn_dist_km"].plot.hist(bins=30)
plt.xlabel("Distance to nearest school (km)")
plt.show()


sns.scatterplot(data=data, x="nn_dist_km", y="pct_change_10yr")
plt.show()



#print(data.columns)
#ax=data.plot()
#unified.plot(ax=ax,facecolor='none')
#secondary.plot(ax=ax,facecolor='none')
#plt.show()


#for column in range(10):
