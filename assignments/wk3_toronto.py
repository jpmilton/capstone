import lxml
import html5lib
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Scrape the data from Wikipedia
url = "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M"
request = requests.get(url)
soup = BeautifulSoup(request.content, 'html.parser')
tables = soup.find_all('table')
df = pd.read_html(str(tables[0]))

# Clean the data
# 1. Ignore cells with borough not assigned

na_rows = df[0].Borough == "Not assigned"
f0 = df[0][~na_rows]

# 3. If Neighbourhood is not assigned then take the borough
pd.set_option('mode.chained_assignment', None)
nb_rows = f0.Neighbourhood == "Not assigned"
f0.loc[nb_rows, 'Neighbourhood'] = f0.loc[nb_rows, 'Borough']
pd.set_option('mode.chained_assignment', 'warn')

# 2. Combined common postcodes. One row with neighbourhoods comma separated

grouped = f0.groupby('Postcode')
ndf = pd.DataFrame(columns=f0.columns)

for postcode, group in grouped:
    g = {}
    g['Postcode'] = postcode
    g['Borough'] = group.Borough.iloc[0]
    g['Neighbourhood'] = ",".join(group['Neighbourhood'].values.tolist())
    ndf = ndf.append(g, ignore_index=True)

print(ndf.shape)
#print(ndf.head())

## Part Two - read the postcodes and join

ll_df = pd.read_csv("../data/Geospatial_Coordinates.csv")
#print(ll_df.head())

j = ndf.merge(ll_df,left_on='Postcode', right_on='Postal Code')
final = j.drop('Postal Code', axis=1)

print(final.head())


## Part Three - Clustering

# import k-means from clustering stage
from sklearn.cluster import KMeans
import folium  # map rendering library

kclusters = 5
k = final.drop(['Borough', 'Neighbourhood','Postcode'], axis=1)
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(k)

# Add the cluster as a column
final.insert(0, 'Cluster', kmeans.labels_)
print(final.head())

# Create a map based on the centroid of the data set
centroid = final.mean(axis=0)
map_clusters = folium.Map(location=[centroid.Latitude, centroid.Longitude], zoom_start=11)

# set color scheme for the clusters
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as colors

colors_array = cm.rainbow(np.linspace(0, 0.7, kclusters))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
#markers_colors = []
for lat, lon, poi, cluster in zip(final['Latitude'], final['Longitude'],
                                  final['Neighbourhood'], final['Cluster']):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[cluster - 1],
        fill=True,
        fill_color=rainbow[cluster - 1],
        fill_opacity=0.7).add_to(map_clusters)

map_clusters

