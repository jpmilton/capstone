import os
import re
import requests
import pandas as pd

from geopy.geocoders import Nominatim
from pandas.io.json import json_normalize
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


# Get the Longitude and Latitude of Brick Lane
address = 'Brick Lane, London, UK'
geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print(latitude, longitude)

# First, let's create the GET request URL. Name your URL url
LIMIT = 100
RADIUS = 2000
url = 'https://api.foursquare.com/v2/venues/explore?client_id={}&client_secret={}&ll={},{}&v={}&query={}&radius={}&limit={}'.format(
    CLIENT_ID, CLIENT_SECRET, latitude, longitude, VERSION, 'Restaurant', RADIUS, LIMIT)
print(url)
results = requests.get(url).json()

venues = results['response']['groups'][0]['items']

nearby_venues = json_normalize(venues)  # flatten JSON

filtered_columns = [
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

print(nearby_venues.head())
print('{} venues were returned by Foursquare.'.format(nearby_venues.shape[0]))

# Analyse the categories
# cat = {}
# groups = nearby_venues.groupby('categories')
# for g in groups:
#     cat[g[0]] = g[1].shape[0]
#
# for c in cat.keys():
#     print(c)

# Categories we are interested in
cuisine = {
    'BBQ Joint': 1,
    'Beer Bar': 1,
    'Breakfast Spot': 1,
    'Café': 1,
    'Coffee Shop': 1,
    'English Restaurant': 1,
    'Falafel Restaurant': 1,
    'Indian Restaurant': 1,
    'Italian Restaurant': 1,
    'Mediterranean Restaurant': 1,
    'Modern European Restaurant': 1,
    'Pizza Place': 1,
    'Portuguese Restaurant': 1,
    'Pub': 1,
    'Restaurant': 1,
    'Seafood Restaurant': 1,
    'Steakhouse': 1,
    'Street Food Gathering': 1,
    'Sushi Restaurant': 1,
    'Vietnamese Restaurant': 1,
}

filtered = nearby_venues.loc[nearby_venues['categories'].isin(cuisine.keys())]
print(filtered.shape)