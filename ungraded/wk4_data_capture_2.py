import os
import re
import requests
import pandas as pd
import numpy as np
import math

from geopy.geocoders import Nominatim
from pandas.io.json import json_normalize



import folium

CLIENT_ID = "QVIXRJUFGBAPDX3SYI03ZE5NKRXHDN0RTDZPKPA2JRKJ23ZR"
CLIENT_SECRET = "XLLUIOXL42E5XG2X5PWOOM4POWBIG1OWI5SQJIKASKYWODMW"  # what
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


def get_venues_df(lat, lng, query):
    # First, let's create the GET request URL. Name your URL url
    LIMIT = 100
    RADIUS = 4000
    url = 'https://api.foursquare.com/v2/venues/explore?client_id={}&client_secret={}&ll={},{}&v={}&query={}&radius={}&limit={}'.format(
        CLIENT_ID, CLIENT_SECRET, lat, lng, VERSION, query, RADIUS, LIMIT)

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

    print (nearby_venues.shape)

    return nearby_venues


def get_venues_expanded(lat, lng):
    init = get_venues_df(lat, lng, 'Restaurant')

    frames = [ init ]
    done = {}

    for cat in init['categories']:pd.concat(frames).drop_duplicates().reset_index(drop=True)
        if cat not in done:
            addendum = get_venues_df(lat, lng, cat)
            print("Cat {} returned {}".format(cat, addendum.shape[0]))
            frames.append(addendum)
            done[cat] = 1

    return pd.concat(frames).drop_duplicates().reset_index(drop=True)



# Get the Longitude and Latitude of Shoreditch Silicon Roundabout
#address = 'Shoreditch, London, UK'
address = 'Brick Lane, London, UK'
geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print(latitude, longitude)

non_indian = get_venues_expanded(latitude,longitude)

# non_indian = get_venues_df(latitude, longitude)
# #
# # # Expand the data
# for i in range(0,3):
#     bl_max = non_indian.max(axis=0, numeric_only=True)
#     bl_min = non_indian.min(axis=0, numeric_only=True)
#     ds0 = get_venues_df(bl_max.lat, bl_max.lng)
#     ds1 = get_venues_df(bl_max.lat, bl_min.lng)
#     ds2 = get_venues_df(bl_min.lat, bl_min.lng)
#     ds3 = get_venues_df(bl_min.lat, bl_max.lng)
#
#     frames = [non_indian, ds0, ds1, ds2, ds3]
#
#     non_indian = pd.concat(frames).drop_duplicates().reset_index(drop=True)
#
# # Ensure correct categories
print('{} unique venues in combined dataset.'.format(non_indian.shape[0]))

non_indian = non_indian[non_indian.categories != 'Indian Restaurant']
print('{} unique venues excluding Indian.'.format(non_indian.shape[0]))

# Approximate conversion of lng/lat to metres
# http://en.wikipedia.org/wiki/Lat-lon
km_per_deg_lat = (111132.92 - 559.82 * math.cos( 2 * latitude ) + 1.175 * math.cos( 4 * latitude))/1000
km_per_deg_lon = (111412.84 * math.cos ( latitude ) - 93.5 * math.cos( 3 * latitude ))/1000

# Create a new column for distance
non_indian = non_indian.assign(dist=np.sqrt((km_per_deg_lat * (non_indian.lat - latitude)) ** 2 + (km_per_deg_lon * (non_indian.lng - longitude)) ** 2))

non_indian.to_csv("../data/non_indian_brick_lane.csv")
