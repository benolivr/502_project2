import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import osmnx as ox
import networkx as nx
from shapely import make_valid
from rasterio.plot import show
import matplotlib.colors as colors
import numpy as np

#get our data
data=gpd.read_file("MontanaSchoolDistricts_shp/MontanaSchoolDistricts_shp/Secondary.shp")
schools=gpd.read_file("MontanaSchools/MontanaSchools.shp")
population=gpd.read_file("clipped_pop.gpkg")

#set index and find helena school district
data=data.set_index("NAME", drop=False)
helena = data.loc[["HELENA HIGH SCHOOL"]]

schools = schools.to_crs(helena.crs)

#set schools index and find target schools
schools=schools.set_index("NAME", drop=False)
helena_high=schools.loc[["Helena High School"]]
capital_high=schools.loc[["Capital High School"]]


#set and trim population
pop = population.to_crs(helena.crs)
district = helena.union_all()
pop = pop[pop.centroid.within(district)].copy()
pop["geometry"] = pop.geometry.centroid

#reprojects helena school districts to lat./long., combines it into one shape and gets road from opsm
G = ox.graph_from_polygon(helena.to_crs(4326).union_all(), network_type="drive")
#changes crs back to be usable
G = ox.project_graph(G, to_crs=helena.crs)
#adds atributes
G = ox.routing.add_edge_speeds(G)
G = ox.routing.add_edge_travel_times(G)


#creates sources(schools) and plots the schools to the nearest intersection to allow for driving calculation
sources = []
for school in [helena_high, capital_high]:
    x = school.geometry.x.iloc[0]
    y = school.geometry.y.iloc[0]
    sources.append(ox.distance.nearest_nodes(G, x, y))


#calculates times
times = nx.multi_source_dijkstra_path_length(G.reverse(copy=False), sources, weight="travel_time")
times_combined = nx.single_source_dijkstra_path_length(G.reverse(copy=False), sources[1], weight="travel_time")


#changes graph to data frame for anylisis
edges = ox.graph_to_gdfs(G, nodes=False)
edges["minutes"] = [times.get(u, float("nan")) / 60 for u in edges.index.get_level_values("u")]
edges["minutes_combined"]=[times_combined.get(u, float("nan")) / 60 for u in edges.index.get_level_values("u")]

#plot stuff
ax = edges.plot(column="minutes", cmap="RdYlGn_r", linewidth=1, legend=True,
                legend_kwds={"label": "Minutes to nearest school"}, figsize=(10, 10))
helena.plot(ax=ax, facecolor="none", edgecolor="black")
helena_high.plot(ax=ax, color="blue", markersize=60)
capital_high.plot(ax=ax, color="blue", markersize=60)


#pop.plot(ax=ax)

plt.show()
ax = edges.plot(column="minutes_combined", cmap="RdYlGn_r", linewidth=1, legend=True,
                legend_kwds={"label": "Minutes to nearest school"}, figsize=(10, 10))
helena.plot(ax=ax, facecolor="none", edgecolor="black")
#helena_high.plot(ax=ax, color="blue", markersize=60)
capital_high.plot(ax=ax, color="blue", markersize=60)
plt.show()




#Weighting done with Claude. 
POP_COL = "population"   # change to whatever your count column is called

pop = population.to_crs(helena.crs)

# use polygon centroids as representative points (skip if already points)
pop[POP_COL]=pop[POP_COL] * pop.geometry.area
pop["geometry"] = pop.geometry.centroid

# snap each point to the nearest intersection and look up its travel time
pop["node"] = ox.distance.nearest_nodes(G, pop.geometry.x.values, pop.geometry.y.values)
pop["minutes"] = pop["node"].map(times) / 60
pop["minutes_combined"] = pop["node"].map(times_combined) / 60

# drop anything that couldn't reach a school
pop = pop.dropna(subset=["minutes"])

def weighted_quantile(values, weights, q):
    order = np.argsort(values)
    v = np.asarray(values)[order]
    w = np.asarray(weights)[order]
    cum = np.cumsum(w) / w.sum()
    return np.interp(q, cum, v)

w = pop[POP_COL]



def asign_data(column):
    return {
        "Population-weighted mean": np.average(pop[column], weights=w),
        "Population-weighted median": weighted_quantile(pop[column], w, 0.5),
        "90th percentile": weighted_quantile(pop[column], w, 0.9),
        "Share within 10 min": w[pop[column] <= 10].sum() / w.sum(),
    }


current_stats = asign_data("minutes")
combined_stats = asign_data("minutes_combined")

driving_dataframe = pd.DataFrame(
    [
        {"Scenario": "Current", **current_stats},
        {"Scenario": "Combined", **combined_stats},
    ]
)

print(driving_dataframe.to_string(index=False))
print(f"Median Precent Change in Drive Time: {(driving_dataframe.loc[0]["Population-weighted mean"]/driving_dataframe.loc[1]["Population-weighted mean"])*100}%")
print(f"Median Change in Drive Time: {(driving_dataframe.loc[1]["Population-weighted mean"])-driving_dataframe.loc[0]["Population-weighted mean"]} minutes")
