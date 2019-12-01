import os
import re
import requests
import pandas as pd
import numpy as np
import math

from geopy.geocoders import Nominatim
from pandas.io.json import json_normalize
from sklearn.cluster import KMeans

import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt  # plotting library

import folium

CLIENT_ID = "QVIXRJUFGBAPDX3SYI03ZE5NKRXHDN0RTDZPKPA2JRKJ23ZR"
CLIENT_SECRET = "XLLUIOXL42E5XG2X5PWOOM4POWBIG1OWI5SQJIKASKYWODM"  # what
VERSION = "20180604"
LIMIT = 5


def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']

    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']

def calc_distance(lat1,lon1,lat2,lon2):
  earth = 6371 # Radius of the earth in km
  dLat = math.radians(lat2-lat1)
  dLon = math.radians(lon2-lon1)
  a = math.sin(dLat/2) * math.sin(dLat/2) +math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *math.sin(dLon/2) * math.sin(dLon/2)

  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));
  d = 1000* earth * c  #Distance in m

  return d


def get_venues_df(lat, lng):
    # First, let's create the GET request URL. Name your URL url
    LIMIT = 100
    RADIUS = 2000
    url = 'https://api.foursquare.com/v2/venues/explore?client_id={}&client_secret={}&ll={},{}&v={}&query={}&radius={}&limit={}'.format(
        CLIENT_ID, CLIENT_SECRET, lat, lng, VERSION, 'Indian', RADIUS, LIMIT)

    results = requests.get(url).json()

    venues = results['response']['groups'][0]['items']

    nearby_venues = json_normalize(venues)  # flatten JSON

    filtered_columns = [
        'venue.id',
        'venue.name',
        'venue.categories',
        'venue.location.lat',
        'venue.location.lng',
        'venue.location.postalCode'
    ]

    nearby_venues = nearby_venues.loc[:, filtered_columns]

    # filter the category for each row
    nearby_venues['venue.categories'] = nearby_venues.apply(get_category_type, axis=1)

    # clean columns
    nearby_venues.columns = [col.split(".")[-1] for col in nearby_venues.columns]

    return nearby_venues


# Get the Longitude and Latitude of Brick Lane
address = 'Brick Lane, London, UK'
geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print(latitude, longitude)

# Approximate conversion of lng/lat to metres
# http://en.wikipedia.org/wiki/Lat-lon
km_per_deg_lat = (111132.92 - 559.82 * math.cos( 2 * latitude ) + 1.175 * math.cos( 4 * latitude))/1000
km_per_deg_lon = (111412.84 * math.cos ( latitude ) - 93.5 * math.cos( 3 * latitude ))/1000

#brick_lane = get_venues_df(latitude, longitude)

all_indian = pd.read_csv("../data/ratings.csv", index_col=0)
print('{} unique venues in combined dataset.'.format(all_indian.shape[0]))

# Calculate distance from each venue to brick lane lat,lng as a new column
all_indian = all_indian.assign(dist=np.sqrt((km_per_deg_lat*(all_indian.lat-latitude))**2 + (km_per_deg_lon*(all_indian.lng-longitude))**2))

# Histogram
hist_dist = all_indian.hist(column='dist', bins=20)
plt.show()

scatter_rating_dist = all_indian.plot.scatter('dist','rating')
plt.show()

all_indian.drop(['postalCode', 'name', 'categories', 'id'], 1)



g3 = all_indian.drop(['postalCode', 'name', 'categories', 'id'], 1)

kclusters = 5
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(g3)
g2 = all_indian
g2.insert(0, 'Cluster Labels', kmeans.labels_)

# create map
map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i * x) ** 2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, cluster in zip(g2['lat'], g2['lng'], g2['Cluster Labels']):
    label = folium.Popup(' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[cluster - 1],
        fill=True,
        fill_color=rainbow[cluster - 1],
        fill_opacity=0.7).add_to(map_clusters)

map_clusters
