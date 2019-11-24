import os
import re
import requests
import pandas as pd
import numpy as np

from geopy.geocoders import Nominatim
from pandas.io.json import json_normalize
from sklearn.cluster import KMeans

import matplotlib.cm as cm
import matplotlib.colors as colors

import folium

CLIENT_ID = "QVIXRJUFGBAPDX3SYI03ZE5NKRXHDN0RTDZPKPA2JRKJ23ZR"
CLIENT_SECRET = "XLLUIOXL42E5XG2X5PWOOM4POWBIG1OWI5SQJIKASKYWODMW"  # what
VERSION = "20180604"
LIMIT = 5

re_postcode = re.compile("\w+\d+\s+\d+\w+")


def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']

    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


def get_postcode(row):
    formatted_address = row['venue.location.formattedAddress']
    postcode = None
    for line in formatted_address:
        if re_postcode.search(line):
            postcode = line
    return postcode


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


def get_venue_rating(id):
    url = 'https://api.foursquare.com/v2/venues/{}?client_id={}&client_secret={}&v={}'.format(id, CLIENT_ID,
                                                                                              CLIENT_SECRET, VERSION)
    results = requests.get(url).json()
    return results['response']['venue']['rating']


def get_venue_ratings(ids):
    ratings = []
    for id in ids:
        url = 'https://api.foursquare.com/v2/venues/{}?client_id={}&client_secret={}&v={}'.format(id, CLIENT_ID,
                                                                                                  CLIENT_SECRET,
                                                                                                  VERSION)
        results = requests.get(url).json()
        try:
            rating = results['response']['venue']['rating']
        except:
            print("{} not rated".format(id))
            rating = None
        ratings.append(rating)

    return ratings


# Get the Longitude and Latitude of Brick Lane
address = 'Brick Lane, London, UK'
geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print(latitude, longitude)

brick_lane = get_venues_df(latitude, longitude)

# Expand the data
# bl_max = brick_lane.max(axis=0, numeric_only=True)
# bl_min = brick_lane.min(axis=0, numeric_only=True)
# ds0 = get_venues_df(bl_max.lat, bl_max.lng)
# ds1 = get_venues_df(bl_max.lat, bl_min.lng)
# ds2 = get_venues_df(bl_min.lat, bl_min.lng)
# ds3 = get_venues_df(bl_min.lat, bl_max.lng)

# frames = [brick_lane, ds0, ds1, ds2, ds3]
# all_indian = pd.concat(frames).drop_duplicates().reset_index(drop=True)
all_indian = brick_lane
# Ensure correct categories
all_indian = all_indian[all_indian.categories == 'Indian Restaurant']
print('{} unique venues in combined dataset.'.format(all_indian.shape[0]))

# Obtain Rating
# ratings = []
gunpowdr = all_indian.iloc[1]['id']
# all_indian[all_indian.name == 'Gunpowder'
print( get_venue_rating(gunpowdr))
# print("{}".format(gunpowdr))
ids = all_indian['id'].values
ratings = get_venue_ratings(ids)
print(ratings)

# # Analyse the categories
# cat = {}
# groups = all.groupby('categories')
# for g in groups:
#     cat[g[0]] = g[1].shape[0]
#
# for c in cat.keys():
#     print(c, cat[c])
#
# # Categories we are interested in
#
# bl_onehot = pd.get_dummies(all[['categories']], prefix="", prefix_sep="")
# all_plus = pd.concat([all,bl_onehot], axis=1)
# g2 = all_plus.groupby('postalCode').mean().reset_index()
#

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
