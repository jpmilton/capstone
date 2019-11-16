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

