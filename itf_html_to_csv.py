from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from constants import *
import pandas as pd
import json
import pprint
import time
import os
import requests

TEST = True
with open('env.json','r') as env_file:
    NEAR_AIRPORTS_API = dict(json.load(env_file))['uri']

def get_5_nearest_airports(town, country):
    response = requests.get(f'{NEAR_AIRPORTS_API}/{town}-{country}')
    if response.status_code == 200:
        return list(response.json())
    else:
        response.raise_for_status()

# All I can gather from the ITF website
tournie_links = []
tournie_ids = []
return_dates = [] # isoformat 8601 at 12am. This is when main draw starts, when you'll probs return.
sign_up_dates = [] # isoformat 8601 with 18:00 time
countries = []
towns = []
nearest_airports = []

for filename in os.listdir('tournie-months'):
    file_path = os.path.join('tournie-months', filename)
    with open(file_path,'r') as html_file:
        soup = BeautifulSoup(html_file, 'html.parser')
        tbody = soup.find('tbody')
        t_rows = tbody.find_all('tr')
        
        k = 0
        skip_outer_loop = False
        for row in t_rows:
            for text in row.strings:
                if text == 'Cancelled':
                    skip_outer_loop = True
                    break
            
            if skip_outer_loop:
                skip_outer_loop = False
                continue

            tournie_link = 'https://www.itftennis.com' + str(row.find('a')['href'])
            index_of_id = tournie_link.index('m-itf')
            tournie_id = tournie_link[index_of_id:-1]
            tournie_links.append(tournie_link)
            tournie_ids.append(tournie_id)
            
            start_date_str = str(row.find('span', class_='date').string)[DATE_SLICE_START:DATE_SLICE_END]
            start_month_str = str(row.find('span', class_='date').string)[MONTH_SLICE_START:MONTH_SLICE_END]
            start_year_str = str(row.find('span', class_='date').string)[YEAR_SLICE_START:YEAR_SLICE_END]
            
            start_date_obj = datetime(int(start_year_str), int(MONTHS_ARRAY[start_month_str]), int(start_date_str))
            sign_up_date_obj = start_date_obj.replace(hour=18) - timedelta(days=2)
            
            return_dates.append(start_date_obj.isoformat())
            sign_up_dates.append(sign_up_date_obj.isoformat())

            country = next(row.find('span', class_='hostname').strings).strip()
            countries.append(country.lower())

            town = row.find('span', class_='location').string.strip()
            towns.append(town.lower())

            nearest_airports.append(get_5_nearest_airports(town, country))
            time.sleep(0.3)

            if TEST: k += 1
            if k > 5:
                break

        index_length = len(tournie_links)
        df = pd.DataFrame({
            'Tournament Link': tournie_links,
            'Tournie_ID': tournie_ids,
            'Sign Up Date': sign_up_dates,
            'Return Date': return_dates,
            'Country': countries,
            'Town': towns,
            'Nearest Airports': nearest_airports,
            'Return Flights Price': index_length * [0]
        })
        df.to_csv('test-data.csv', index=True) if TEST else df.to_csv('data.csv', index=True)
                