import os
import re
import requests
import pandas as pd
import numpy as np

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


def get_venues_df(lat, lng):
    # First, let's create the GET request URL. Name your URL url
    LIMIT = 100
    RADIUS = 200
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
    rt = None

    try:
        rt = results['response']['venue']['rating']
    except:
        if results['meta']['code'] == 429:
            raise ValueError("Foursquare quota exceed")
            #os.sys.exit()
        else:
            raise ValueError("{} not rated".format(id))
        rt = None

    return rt


# def get_venue_ratings(ids):
#     ratings = []
#     for id in ids:
#         url = 'https://api.foursquare.com/v2/venues/{}?client_id={}&client_secret={}&v={}'.format(id, CLIENT_ID,
#                                                                                                   CLIENT_SECRET,
#                                                                                                   VERSION)
#         results = requests.get(url).json()
#         try:
#             rating = results['response']['venue']['rating']
#         except:
#             print("{} not rated".format(id))
#             rating = None
#         ratings.append(rating)
#
#     return ratings


# Get the Longitude and Latitude of Brick Lane
address = 'Brick Lane, London, UK'
geolocator = Nominatim(user_agent="foursquare_agent")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print(latitude, longitude)

# brick_lane = get_venues_df(latitude, longitude)
# #
# # # Expand the data
# bl_max = brick_lane.max(axis=0, numeric_only=True)
# bl_min = brick_lane.min(axis=0, numeric_only=True)
# ds0 = get_venues_df(bl_max.lat, bl_max.lng)
# ds1 = get_venues_df(bl_max.lat, bl_min.lng)
# ds2 = get_venues_df(bl_min.lat, bl_min.lng)
# ds3 = get_venues_df(bl_min.lat, bl_max.lng)
#
# frames = [brick_lane, ds0, ds1, ds2, ds3]
#
# for d in frames:
#     print(d.shape)
#
# all_indian = pd.concat(frames).drop_duplicates().reset_index(drop=True)
# # Ensure correct categories
# all_indian = all_indian[all_indian.categories == 'Indian Restaurant']

#all_indian = pd.read_csv("../data/brick_lane.csv")
all_indian = pd.read_csv("../data/ratings.csv")

print('{} unique venues in combined dataset.'.format(all_indian.shape[0]))

# Add column 'ratings' and populate with None
#ratings = [None] * all_indian.shape[0]
#all_indian = all_indian.assign(rating = ratings)


#ids = all_indian[all_indian.rating == 'None']['id'].values
# ratings = get_venue_ratings(ids)
ids = all_indian['id'].values
rts = all_indian['rating'].values

for id,rating in zip(ids,rts):
    if rating<0:
        print("Fetch {},{}".format(id,rating))
        try:
            r = get_venue_rating(id)
        except ValueError as err:
            print(err.args)
            r = -2

        all_indian.loc[all_indian.id==id,'rating'] = r


# Save updated dataframe
all_indian.to_csv("../data/ratings.csv")

# Obtain Rating
# ratings = []
#gunpowdr = all_indian.iloc[1]['id']
# # all_indian[all_indian.name == 'Gunpowder'
#print( get_venue_rating(gunpowdr))
# # print("{}".format(gunpowdr))
# ids = all_indian['id'].values
# ratings = get_venue_ratings(ids)
# print(ratings)

