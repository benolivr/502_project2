import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import osmnx as ox
import networkx as nx
import numpy as np

#get our data
data_unified=gpd.read_file("MontanaSchoolDistricts_shp/MontanaSchoolDistricts_shp/Unified.shp")
data_secondary=gpd.read_file("MontanaSchoolDistricts_shp/MontanaSchoolDistricts_shp/Secondary.shp")
schools=gpd.read_file("MontanaSchools/MontanaSchools.shp")
population=gpd.read_file("clipped_population_Central.gpkg")

#set index and find geyser school district
data_unified=data_unified.set_index("NAME", drop=False)
data_secondary=data_secondary.set_index("NAME", drop=False)
schools=schools.set_index("NAME", drop=False)


geyser = data_unified.loc[["GEYSER K-12"]]
belt= data_secondary.loc[["BELT HIGH SCHOOL"]]
stanford= data_unified.loc[["STANFORD K-12 SCHOOLS"]]
districts=[geyser,belt,stanford]

combined = gpd.GeoDataFrame(pd.concat(districts, ignore_index=True))

schools = schools.to_crs(geyser.crs)
geyser_high=schools.loc[["Geyser High School"]]
belt_high=schools.loc[["Belt High School"]]
stanford_high=schools.loc[["Stanford High School"]]

schools=[geyser_high,belt_high,stanford_high]


#set and trim population
pop = population.to_crs(combined.crs)
district = combined.union_all()
pop = pop[pop.centroid.within(district)].copy()
pop["geometry"] = pop.geometry.centroid


#reprojects helena school districts to lat./long., combines it into one shape and gets road from opsm
G = ox.graph_from_polygon(combined.to_crs(4326).union_all(), network_type="drive")
#changes crs back to be usable
G = ox.project_graph(G, to_crs=combined.crs)
#adds atributes
G = ox.routing.add_edge_speeds(G)
G = ox.routing.add_edge_travel_times(G)

#creates sources(schools) and plots the schools to the nearest intersection to allow for driving calculation
sources = []
for school in schools:
    x = school.geometry.x.iloc[0]
    y = school.geometry.y.iloc[0]
    sources.append(ox.distance.nearest_nodes(G, x, y))

    #calculates times
times = nx.multi_source_dijkstra_path_length(G.reverse(copy=False), sources, weight="travel_time")
times_combined_largest = nx.single_source_dijkstra_path_length(G.reverse(copy=False), sources[1], weight="travel_time")
times_combined_central = nx.single_source_dijkstra_path_length(G.reverse(copy=False), sources[0], weight="travel_time")



#changes graph to data frame for anylisis
edges = ox.graph_to_gdfs(G, nodes=False)
edges["minutes"] = [times.get(u, float("nan")) / 60 for u in edges.index.get_level_values("u")]
edges["minutes_combined_largest"] = [times_combined_largest.get(u, float("nan")) / 60 for u in edges.index.get_level_values("u")]
edges["minutes_combined_central"] = [times_combined_central.get(u, float("nan")) / 60 for u in edges.index.get_level_values("u")]


#plot stuff
ax = edges.plot(column="minutes", cmap="RdYlGn_r", linewidth=1, legend=True,
                legend_kwds={"label": "Minutes to nearest school"}, figsize=(10, 10))

for district in districts:
    district.plot(ax=ax, facecolor="none", edgecolor="black")

for school in schools:
    school.plot(ax=ax, color="blue", markersize=60)

plt.show()




#Weighting done with Claude. 
POP_COL = "population"   # change to whatever your count column is called

# pop is already centroid points from the earlier trim step, and the
# population column is already a count per hexagon, so no reweighting needed


pop["node"] = ox.distance.nearest_nodes(G, pop.geometry.x.values, pop.geometry.y.values)
pop["minutes"] = pop["node"].map(times) / 60
pop["minutes_combined_largest"] = pop["node"].map(times_combined_largest) / 60
pop["minutes_combined_central"] = pop["node"].map(times_combined_central) / 60

# drop anything that can't reach a school in ANY scenario
before = len(pop)
pop = pop.dropna(subset=["minutes", "minutes_combined_largest", "minutes_combined_central"])
print(f"Dropped {before - len(pop):,} of {before:,} points with no route")

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
combined_largest=asign_data("minutes_combined_largest")
combined_central=asign_data("minutes_combined_central")

driving_dataframe = pd.DataFrame(
    [
        {"Scenario": "Current", **current_stats},
        {"Scenario": "Combined into Largest",**combined_largest},
        {"Scenario": "Combined into Central",**combined_central}
    ]
)

print(driving_dataframe.to_string(index=False))
