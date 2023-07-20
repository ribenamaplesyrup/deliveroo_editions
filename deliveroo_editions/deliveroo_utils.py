# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/deliveroo_utils.ipynb.

# %% auto 0
__all__ = ['tags', 'restaurants', 'timestamped_restaurants', 'test_address', 'driver', 'result', 'test_url', 'editions_list',
           'addresses', 'test_editions', 'url', 'get_restaurant_tags', 'get_timestamp', 'add_timestamps_to_restaurants',
           'get_restaurants', 'search_deliveroo', 'results_to_editions_url', 'if_editions', 'get_editions',
           'get_restaurants_from_editions_location', 'get_editions_locations_near_addresses', 'remove_time_from_url',
           'get_address_from_restaurant_url']

# %% ../nbs/deliveroo_utils.ipynb 2
from .selenium_utils import *
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from ratelimit import limits, RateLimitException, sleep_and_retry
import time

# %% ../nbs/deliveroo_utils.ipynb 3
@sleep_and_retry
# @limits(calls=1, period=20)
# @limits(calls=1, period=4)
def get_restaurant_tags(url:str, # URL for Deliveroo restaurants page
                        driver=None
                       ):
    "Returns all list elements from Deliveroo restaurants webpage corresponding to a restaurant"
    if not driver:
        driver = initialise_driver(service,False)
    # time.sleep(1)
    driver.get(url)
    wait = WebDriverWait(driver, 3)  # Maximum wait time in seconds
    ul_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[class*="HomeFeedGrid"]')))
    soup = BeautifulSoup(ul_element.get_attribute('innerHTML'), 'html.parser')
    filtered_li_tags = [li for li in soup.find_all('li') if not li.find_parents('li')]
    return filtered_li_tags

tags = get_restaurant_tags("https://web.archive.org/web/20201019/https://deliveroo.co.uk/restaurants/brighton/brighton-editions?tags=deliveroo+editions")
assert len(tags) == 13

# %% ../nbs/deliveroo_utils.ipynb 4
def get_timestamp(url:str # URL for Deliveroo
                 ):
                     "Returns YYYYMMDD timestamp from url of format: https://web.archive.org/web/YYYYMMDD/"
                     timestamp = url.split('/')[4]
                     if timestamp.isdigit():
                         return timestamp[0:8]
                     else:
                         print("Could not extract timestamp of format YYYYMMDD from url provided")
                         return

assert get_timestamp("https://web.archive.org/web/20201019/https://deliveroo.co.uk/restaurants/brighton/brighton-editions?tags=deliveroo+editions")

# %% ../nbs/deliveroo_utils.ipynb 5
def add_timestamps_to_restaurants(restaurants, url):
    for restaurant in restaurants: 
        restaurant['timestamp_url'] = url
        restaurant['timestamp'] = get_timestamp(url)
    return restaurants


restaurants = [{'name': 'Oowee Vegan',
  'location': 'brighton-editions',
  'restaurant_url': 'https://deliveroo.co.uk/menu/brighton/brighton-editions/oowee-vegan-editions-bnc?day=today&geohash=gcpc5qr68ee1&time=ASAP'}]

timestamped_restaurants = [{'name': 'Oowee Vegan',
  'location': 'brighton-editions',
  'timestamp': '20201019',
  'restaurant_url': 'https://deliveroo.co.uk/menu/brighton/brighton-editions/oowee-vegan-editions-bnc?day=today&geohash=gcpc5qr68ee1&time=ASAP',
  'timestamp_url': 'https://web.archive.org/web/20201019/https://deliveroo.co.uk/restaurants/brighton/brighton-editions?tags=deliveroo+editions'}]

assert add_timestamps_to_restaurants(restaurants, timestamped_restaurants[0]['timestamp_url']) == timestamped_restaurants

# %% ../nbs/deliveroo_utils.ipynb 6
def get_restaurants(url:str, # URL for Deliveroo restaurants page
                    # headless:bool=True,
                    driver= None
                   ): # run headless (True) or with browser (False).
                       """Gets the restaurant `name`, editions `location` and Deliveroo `restaurant_url`
                       for each restaurant on url page."""
                       if not driver:
                           driver = initialise_driver(service,True)
                       restaurants = []
                       tags = get_restaurant_tags(url, driver)
                       # timestamp = get_timestamp(url)
                       for tag in tags:
                           name, restaurant_url, location = "", "", ""
                           list_sections = tag.find_all('ul')
                           if list_sections:
                               for list_section in list_sections:
                                   list_items = list_section.find_all('li')
                                   if len(list_items) >= 3:
                                       name = list_items[0].text
                                       try:
                                           restaurant_url = tag.find_all('a')[0]['href']
                                           if restaurant_url.startswith('/menu'):
                                               restaurant_url = "https://deliveroo.co.uk" + restaurant_url
                                           location = restaurant_url.split("/")[4]
                                           edition = restaurant_url.split("/")[5]
                                       except Exception as e: 
                                           print(e)
                                           print(f"Couldn't get metadata for {name} in {url}")
                                           # restaurants.append({'name': name, 'location': location, 'timestamp': timestamp, 'restaurant_url': restaurant_url, 'timestamp_url': url})
                                       restaurants.append({'name': name, 'location': location, 'edition': edition, 'restaurant_url': restaurant_url})

                                   else:
                                       pass
                           else:
                               print(f"No restaurants found at {url}")
                       return restaurants

# %% ../nbs/deliveroo_utils.ipynb 8
def search_deliveroo(address:str, # UK address containing a UK postcode
                     driver= None  # Initialised Selenium webdriver
                    ):
                        """Searches Deliveroo for an address, returning webdriver element once search results page has loaded."""
                        base_url = "https://deliveroo.co.uk/"
                        if not driver:
                            driver = initialise_driver(service,True)
                        driver.get(base_url)
                        wait = WebDriverWait(driver, 3)  # Maximum wait time in seconds
                        input_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input#location-search')))
                        input_element.send_keys(address)
                        input_element.send_keys(Keys.RETURN)
                        try:
                            wait = WebDriverWait(driver, 3)
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[class*="HomeFeedGrid"]')))
                            return driver, True
                        except:
                            print(f"Deliveroo may not be at {address} yet.")
                            return driver, False

test_address = "144 Cambridge Heath Rd, Bethnal Green, London E1 5QJ"
driver, result = search_deliveroo(test_address)
assert driver.current_url in ["https://deliveroo.co.uk/restaurants/london/stepney-green?fulfillment_method=DELIVERY&geohash=gcpvng8jvn74", "https://deliveroo.co.uk/restaurants/london/stepney-green/?fulfillment_method=DELIVERY&geohash=gcpvng8jvn74"]

# %% ../nbs/deliveroo_utils.ipynb 9
driver = initialise_driver(service,False)
test_address = "Aviemore Centre, Aviemore Centre, Aviemore PH22 1PF, UK"
driver, result = search_deliveroo(test_address, driver)

# %% ../nbs/deliveroo_utils.ipynb 10
driver = initialise_driver(service,True)
test_address = "AB3 9HR"
driver, result = search_deliveroo(test_address, driver)

# %% ../nbs/deliveroo_utils.ipynb 11
driver = initialise_driver(service,False)
test_address = "UB8 1AA"
driver, result = search_deliveroo(test_address, driver)

# %% ../nbs/deliveroo_utils.ipynb 12
def results_to_editions_url(url:str, # Deliveroo search results url
                           ):
                               "Apply `deliveroo+editions` filter to Deliveroo search results url"
                               return url.split('?')[0] + '?fulfillment_method=DELIVERY&tags=deliveroo+editions'

test_url = 'https://deliveroo.co.uk/restaurants/london/stepney-green?fulfillment_method=DELIVERY&geohash=gcpvng8jvn74'
assert results_to_editions_url(test_url) == "https://deliveroo.co.uk/restaurants/london/stepney-green?fulfillment_method=DELIVERY&tags=deliveroo+editions"

# %% ../nbs/deliveroo_utils.ipynb 13
def if_editions(test_url, # editions url
                driver=None
               ):
    "Check if results page includes editions"
    if not driver:
        driver = initialise_driver(service,True)
    driver.get(test_url)
    try:
        wait = WebDriverWait(driver, 10)
        nav_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[class*="FilterTag"]')))
        if nav_element.find_element(By.XPATH, "//p[text()='Deliveroo Editions']"):
            # driver.close()
            return driver, True
    except:
        # driver.close()
        return driver, False   

driver, result = if_editions('https://deliveroo.co.uk/restaurants/inverness/inverness?fulfillment_method=DELIVERY&geohash=gfhyzze8kc7x&tags=deliveroo+editions')
assert not result
driver, result = if_editions('https://deliveroo.co.uk/restaurants/edinburgh/calton?fulfillment_method=DELIVERY&tags=deliveroo+editions')
assert result

# %% ../nbs/deliveroo_utils.ipynb 14
def get_editions(url:str, # URL for Deliveroo search results page
                    # headless:bool=True,
                    driver= None
                   ): # run headless (True) or with browser (False).
                       """Returns a list of editions location
                       from all the editions restaurants on url page ie 'bristol-editions'."""
                       if not driver:
                           driver = initialise_driver(service,False)
                       editions_url = results_to_editions_url(url)
                       editions_list = []
                       driver, result = if_editions(editions_url, driver=driver)
                       if result:
                           tags = get_restaurant_tags(editions_url, driver=driver)
                           for tag in tags:
                               edition_tags = tag.find_all('a')[0]['href'].split('/')
                               edition = edition_tags[2].lower() + '/' + edition_tags[3].lower()
                               if edition not in editions_list:
                                   editions_list.append(edition)
                           return editions_list
                       else:
                           return editions_list

# %% ../nbs/deliveroo_utils.ipynb 17
def get_restaurants_from_editions_location(editions_list:list # list of editions locations ie ['london/whitechapel-editions','london/canary-wharf']
                                          ):
                                              "gets restaurant metadata for all restaurants based at listed editions locations"
                                              restaurants = []
                                              for edition in editions_list:
                                                  edition_url = "https://deliveroo.co.uk/restaurants/" + edition + "?fulfillment_method=DELIVERY&tags=deliveroo+editions"
                                                  restaurants += get_restaurants(edition_url)
                                              return restaurants    

editions_list = ['london/fish-island-area','london/blackwall']
restaurants = get_restaurants_from_editions_location(editions_list)
assert restaurants

# %% ../nbs/deliveroo_utils.ipynb 18
def get_editions_locations_near_addresses(addresses:list,  # list of address strings to search Deliveroo's website for
                                          driver= None 
                                ):
                                    "Returns a list of all editions locations found when searching all the restaurants at or near the list of addresses"
                                    if not driver:
                                        driver = initialise_driver(service,True)
                                    editions_locations = []
                                    for i, address in enumerate(addresses):
                                        driver, result = search_deliveroo(address, driver=driver)
                                        if result:
                                            editions = get_editions(driver.current_url, driver=driver)   
                                            if editions:
                                                editions_locations.extend([item for item in editions if item not in editions_locations])
                                    return editions_locations

addresses = ['144 Cambridge Heath Rd, Bethnal Green, London E1 5QJ',
            '20 Fonthill Rd, Finsbury Park, London N4 3HU']
test_editions = ['london/whitechapel-editions',
 'london/canary-wharf',
 'london/caledonian-road-and-barnsbury',
 'london/canning-town-editions',
 'london/fish-island-area',
 'london/blackwall',
 'london/hornsey-station',
 'london/kentish-town',
 'london/wood-green']

assert any(edition_location in test_editions for edition_location in get_editions_locations_near_addresses(addresses))

# %% ../nbs/deliveroo_utils.ipynb 19
def remove_time_from_url(url):
    url = url.replace("day=today", "")
    url = url.replace("day=tomorrow", "")
    split_url = url.split('&')
    if "time=" in split_url[-1]:
        return "".join(url.split('&')[0:-1])
    else:
        return url

# %% ../nbs/deliveroo_utils.ipynb 20
def get_address_from_restaurant_url(url:str,  # Deliveroo URL
                                    driver= None
                                   ):
                                       "scrape restaurant address from Deliveroo page"
                                       driver = initialise_driver(service,True)
                                       url = remove_time_from_url(url)
                                       driver.get(url)
                                       # click element on page to remove pop-up
                                    
                                       attempts = 0
                                       while attempts<2:
                                           try:
                                               wait = WebDriverWait(driver, 10)
                                               nav_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[class*="MenuNavHeader"]')))
                                               nav_element.click()
                                               wait = WebDriverWait(driver, 10)
                                               info_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Info']")))
                                               while info_element is not None:
                                                   try:
                                                       info_button = info_element.find_element("xpath", "./button")
                                                       break
                                                   except:
                                                       info_element = info_element.find_element("xpath", "..")
                                               info_button.click()
                                               wait = WebDriverWait(driver, 10)
                                               map_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-testid*="content-card-map"]')))
                                               attempts = 2
                                           except:
                                               ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                                               attempts += 1
                                       wait = WebDriverWait(driver, 10)
                                       map_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-testid*="content-card-map"]')))
                                       uilines = map_element.find_element("xpath", "..").find_element(By.CSS_SELECTOR, 'div[class*="UILines"]')
                                       address = uilines.text
                                       driver.close()
                                       return address
                                       
url = 'https://deliveroo.co.uk/menu/London/battersea-york-road/jakobs-kitchen-editions-byr-new?day=today&geohash=gcpugcwkyb25&time=ASAP'
assert get_address_from_restaurant_url(url) == 'Unit 13-15, Heliport Industrial Estate, Battersea, London, SW113SS'
