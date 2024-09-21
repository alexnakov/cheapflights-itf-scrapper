from datetime import datetime, timedelta
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from bs4 import BeautifulSoup
from constants import *
import pandas as pd
import time
import requests
import asyncio
import json
import os
import traceback
import pprint
import re

TEST = True

class ChromeDriver(Chrome):
    def __init__(self):
        super().__init__()

    def query_selector_all(self, css_selector, timeout=10, retries=5):
        for attempt in range(retries):
            try:
                elements = WebDriverWait(self, timeout).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
                )
                return elements
            except (NoSuchElementException, StaleElementReferenceException, TimeoutException):
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    raise

if __name__ == '__main__':
    driver = ChromeDriver()
    action_chains = ActionChains(driver, 100)
    df = pd.read_csv('test-data.csv') if TEST else pd.read_csv('data.csv')

    driver.get('https://cheapflights.com'); time.sleep(1) # Then reject cookies
    driver.query_selector_all('button[role="button"]')[-1].click(); 
    time.sleep(1)

    for index, row in df.iterrows():
        air = row['Nearest Airports']
        arrival_airports = ",".join(eval(air)[:3])
    

        dep_date = row['Sign Up Date'][:10]
        return_date = row['Return Date'][:10]

        time.sleep(4)
        url = f'https://cheapflights.co.uk/flight-search/MAN,LON,BHX-{arrival_airports}/{dep_date}/{return_date}'
        
        driver.get(url); time.sleep(3)
        driver.query_selector_all('.bCGf-mod-theme-transparent')[-1].click(); time.sleep(4)

        results_div = driver.query_selector_all('.Fxw9')[0]
        soup = BeautifulSoup(results_div.get_attribute('outerHTML'),'html.parser')
        result_cards = soup.find_all(lambda el: el.has_attr('data-resultid'))
        price = None
        for result in result_cards:
            a = result.find_all(string='Best')
            if len(a) != 0:
                b = result.find('div', re.compile('price-text'))
                price_str = next(b.descendants).text[1:]
                price = int(price_str.strip('"').replace(",", ""))
                break
        df.loc[index,'Return Flights Price'] = price
        df.to_csv('test-data.csv', index=False) if TEST else pd.to_csv('data.csv', index=False)

    driver.quit()


