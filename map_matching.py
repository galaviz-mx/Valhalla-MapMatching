#%% IMPORT LIBRARIES
import folium
import pandas as pd
import geopandas as gpd
import json
import requests
from shapely.geometry.linestring import LineString
from pyproj import Geod
from decode_functions import decode

#%% READ & FORMAT GPS INFO
geojson_file = 'trip_hires.geojson'
gdf_rawGPS_linestring = gpd.read_file(geojson_file)
gdf_rawGPS_points_temp = gdf_rawGPS_linestring.apply(lambda x: [y for y in x['geometry'].coords], axis=1)
gdf_rawGPS_points = gpd.GeoDataFrame(geometry=gpd.points_from_xy([a_tuple[0] for a_tuple in gdf_rawGPS_points_temp[0]], [a_tuple[1] for a_tuple in gdf_rawGPS_points_temp[0]]), crs=4326)
df_rawGPS_points = pd.DataFrame(list(zip([a_tuple[0] for a_tuple in gdf_rawGPS_points_temp[0]],[a_tuple[1] for a_tuple in gdf_rawGPS_points_temp[0]])) , columns=['lon', 'lat'])
gdf_rawGPS = gpd.GeoDataFrame(pd.concat([gdf_rawGPS_linestring, gdf_rawGPS_points], ignore_index=True))

#%% VALHALLA REQUEST
meili_coordinates = df_rawGPS_points.to_json(orient='records')
meili_head = '{"shape":'
meili_tail = ""","search_radius": 300, "shape_match":"map_snap", "costing":"auto", "format":"osrm"}"""
meili_request_body = meili_head + meili_coordinates + meili_tail
url = "http://localhost:8002/trace_route"
headers = {'Content-type': 'application/json'}
data = str(meili_request_body)
r = requests.post(url, data=data, headers=headers)

#%% READ & FORMAT VALHALLA RESPONSE
if r.status_code == 200:
    response_text = json.loads(r.text)
search_1 = response_text.get('matchings')
search_2 = dict(search_1[0])
polyline6 = search_2.get('geometry')
search_3 = response_text.get('tracepoints')

lst_MapMatchingRoute = LineString(decode(polyline6))
gdf_MapMatchingRoute_linestring = gpd.GeoDataFrame(geometry=[lst_MapMatchingRoute], crs=4326)
gdf_MapMatchingRoute_points_temp = gdf_MapMatchingRoute_linestring.apply(lambda x: [y for y in x['geometry'].coords], axis=1)
gdf_MapMatchingRoute_points = gpd.GeoDataFrame(geometry=gpd.points_from_xy([a_tuple[0] for a_tuple in gdf_MapMatchingRoute_points_temp[0]], [a_tuple[1] for a_tuple in gdf_MapMatchingRoute_points_temp[0]]), crs=4326)
gdf_MapMatchingRoute = gpd.GeoDataFrame(pd.concat([gdf_MapMatchingRoute_linestring, gdf_MapMatchingRoute_points], ignore_index=True))
df_mapmatchedGPS_points = pd.DataFrame(list([d['location'] for d in search_3 if 'location' in d]) , columns=['lon', 'lat'])
gdf_mapmatchedGPS_points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df_mapmatchedGPS_points['lon'], df_mapmatchedGPS_points['lat']), crs=4326)

#%% RAW & MAP-MATCHING ROUTES - DRAW MAP
m = folium.Map([22.2783, -97.8643], tiles='cartodbdark_matter', zoom_start=14)
folium.GeoJson(gdf_rawGPS, style_function=lambda x:{'color': 'red'}, marker=folium.CircleMarker(radius=4, weight=0, fill_color='red', fill_opacity=1), name='rawGPS_points').add_to(m)
folium.GeoJson(gdf_mapmatchedGPS_points, marker=folium.CircleMarker(radius=4, weight=0, fill_color='white', fill_opacity=1), name='MapMatching_rawGPS_points').add_to(m)
folium.GeoJson(gdf_MapMatchingRoute, style_function=lambda x:{'color': 'green'}, marker=folium.CircleMarker(radius=4, weight=0, fill_color='green', fill_opacity=1), name='MapMatching_Route').add_to(m)
folium.LayerControl(position='topright', collapsed=False).add_to(m)
m.save('mapmatching.html')

#%% RAW & MAP-MATCHING ROUTES - CALCULATE DISTANCE
geod = Geod(ellps="WGS84")
rawGPS_linestring_distance = geod.geometry_length(gdf_rawGPS_linestring['geometry'][0])
MapMatchingRoute_linestring_distance = geod.geometry_length(gdf_MapMatchingRoute_linestring['geometry'][0])
print('rawGPS_linestring_distance = ', f"{rawGPS_linestring_distance:,.0f}")
print('MapMatchingRoute_linestring_distance = ', f"{MapMatchingRoute_linestring_distance:,.0f}")
# %%
