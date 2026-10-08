import geopandas as gpd
import pandas as pd

SHP = "MontanaSchoolDistricts_shp/MontanaSchoolDistricts_shp"

# the four study districts
secondary = gpd.read_file(f"{SHP}/Secondary.shp").set_index("NAME", drop=False)
unified = gpd.read_file(f"{SHP}/Unified.shp").set_index("NAME", drop=False)
districts = gpd.GeoDataFrame(pd.concat([
    secondary.loc[["DENTON HIGH SCHOOL"]],
    unified.loc[["STANFORD K-12 SCHOOLS", "GERALDINE K-12", "HOBSON K-12 SCHOOLS"]],
]))

# kontur is EPSG:3857; read only the districts' bounding box (+1 km buffer), then clip exactly
district_geom = districts.to_crs(3857).union_all().buffer(1000)
pop = gpd.read_file("kontur_population_US_20231101.gpkg", bbox=tuple(district_geom.bounds))
pop = pop[pop.geometry.intersects(district_geom)]

pop.to_file("clipped_population_Denton_area.gpkg", driver="GPKG")

# sanity check: population per district (hexagon centroids, as the notebook does)
cent = pop.copy()
cent["geometry"] = cent.centroid
for name, row in districts.to_crs(3857).iterrows():
    inside = cent[cent.within(row.geometry)]
    print(f"{name}: {len(inside)} hexes, {inside.population.sum():,.0f} people")
