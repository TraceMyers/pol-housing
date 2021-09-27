# from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN 
# from multiprocessing import Pool, Process, Manager 
# import requests
from bs4 import BeautifulSoup as bsoup
import time
import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

from multiprocessing.dummy import Process, Lock, Queue

# NOTE: zips originally written to unsearched_zips.txt have a population of at
# least 100, which I believe (though I need to investigate) corresponds to
# the 5th percentile of zip code populations
# TODO: NEED thread waiting for input so a quit command can be given and
# exit data can be written, such as rewriting searched and partly searched files

unsearched = []
partly_searched = []

class WaitData:
    def __init__(self):
        self.waits_n = 100

        self.mouseover_wait_mean = 0.12
        self.mouseover_wait_sd = 0.06
        self.mouseover_waits = pd.DataFrame(np.random.normal(
            self.mouseover_wait_mean,
            self.mouseover_wait_sd,
            self.waits_n
        ))
        self.mouseover_waits.iloc[self.mouseover_waits < 0.01] = 0.02
        self.mouseover_waits = np.array(self.mouseover_waits)
        self.mwaits_i = 0

        self.select_wait_mean = 1.8
        self.select_wait_sd = 0.8
        self.select_waits = pd.DataFrame(np.random.normal(
            self.select_wait_mean,
            self.select_wait_sd,
            self.waits_n
        ))
        self.select_waits.iloc[self.mouseover_waits < 0.05] = 0.05
        self.select_waits = np.array(self.select_waits)
        self.swaits_i = 0

        self.typekeys_wait_mean = 0.03
        self.typekeys_wait_sd = 0.02
        self.typekeys_waits = pd.DataFrame(np.random.normal(
            self.typekeys_wait_mean,
            self.typekeys_wait_sd,
            self.waits_n
        ))
        self.typekeys_waits.iloc[self.typekeys_waits < 0.01] = 0.01
        self.typekeys_waits = np.array(self.typekeys_waits)
        self.typekeys_i = 0

        self.long_wait_mean = 15
        self.long_wait_sd = 4
        self.long_waits = pd.DataFrame(np.random.normal(
            self.long_wait_mean,
            self.long_wait_sd,
            self.waits_n
        ))
        self.long_waits.iloc[self.long_waits < 10] = 10
        self.long_waits = np.array(self.long_waits)
        self.long_i = 0

        self.medium_wait_mean = 7
        self.medium_wait_sd = 2
        self.medium_waits = pd.DataFrame(np.random.normal(
            self.medium_wait_mean,
            self.medium_wait_sd,
            self.waits_n
        ))
        self.medium_waits.iloc[self.medium_waits < 2.5] = 2.5
        self.medium_waits = np.array(self.medium_waits)
        self.medium_i = 0

        self.w_mouseover = 0
        self.w_select = 1
        self.w_typekeys = 2
        self.w_medium = 3
        self.w_long = 4

Wait = WaitData()

def do_wait(w_type):
    if w_type == Wait.w_mouseover:
        wait_time = Wait.mouseover_waits[Wait.mwaits_i]
        Wait.mwaits_i += 1
        if Wait.mwaits_i == Wait.waits_n:
            Wait.mwaits_i = 0
    elif w_type == Wait.w_select:
        wait_time = Wait.select_waits[Wait.swaits_i]
        Wait.swaits_i += 1
        if Wait.swaits_i == Wait.waits_n:
            Wait.swaits_i = 0
    elif w_type == Wait.w_typekeys:
        wait_time = Wait.typekeys_waits[Wait.typekeys_i]
        Wait.typekeys_i += 1
        if Wait.typekeys_i == Wait.waits_n:
            Wait.typekeys_i = 0
    elif w_type == Wait.w_medium:
        wait_time = Wait.medium_waits[Wait.medium_i]
        Wait.medium_i += 1
        if Wait.medium_i == Wait.waits_n:
            Wait.medium_i = 0
    elif w_type == Wait.w_long:
        wait_time = Wait.long_waits[Wait.long_i]
        Wait.long_i += 1
        if Wait.long_i == Wait.waits_n:
            Wait.long_i = 0
    else:
        print('ERROR @ do_wait(): bad argument passed')
    time.sleep(wait_time[0])

def load_county_data():
    with open('unsearched_counties.txt', 'r') as unsearched_f:
        for line in unsearched_f:
            unsearched.append(line.strip('\n'))
    
    with open('partly_searched_counties.txt', 'r') as partly_f:
        for line in partly_f:
            colon_i = line.find(':')
            county = line[:colon_i]
            addresses = line[colon_i+1:].split('||')
            addresses[-1] = addresses[-1].strip('\n')
            partly_searched.append((county, addresses))

def get_random_county():
    partly_searched_ct = len(partly_searched)
    if partly_searched_ct > 0:
        selected_county_i = random.randint(0,partly_searched_ct-1)
        ps_county_data = partly_searched[selected_county_i]
        partly_searched.pop(selected_county_i)
        return ps_county_data, True
    unsearched_ct = len(unsearched)
    selected_county_i = random.randint(0, unsearched_ct-1)
    county = unsearched[selected_county_i]
    unsearched.pop(selected_county_i)
    return county, False

def rewrite_county_files_on_exit():
    for ps in partly_searched:
        write_partly_searched_county(ps[0], ps[1])
    os.remove('partly_searched_counties.txt')
    os.rename('partly_searched_temp.txt', 'partly_searched_counties.txt')
    with open('unsearched_counties.txt', 'w') as unsearched_f:
        for i in range(len(unsearched) - 1):
            unsearched_f.write(f'{unsearched[i]}\n')
        unsearched_f.write(f'{unsearched[-1]}')

# remember to close driver on exit or before getting a new one
max_wait = 30
def get_driver(county, driver=None, short_wait=False):
    if driver is None:
        driver = webdriver.Chrome()
    driver.get('http://www.zillow.com')
    try:
        search_box = WebDriverWait(driver, max_wait).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//input[@type="text"]')
        ))
        do_wait(Wait.w_select)
        driver.execute_script('arguments[0].click();', search_box)
    except:
        print('ERROR @ get_webdriver(): One front page, either no input box or cannot click in it. Returning None.')
        return None

    try:
        do_wait(Wait.w_medium)
        for c in county:
            search_box.send_keys(c)
            do_wait(Wait.w_typekeys)
        do_wait(Wait.w_typekeys)
        search_box.send_keys(Keys.RETURN)
    except:
        print('ERROR @ get_webdriver(): Was not able to use search box on front page. Returning None.')
        return None

    try:
        if short_wait:
            for_sale_button = WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable(
                (By.XPATH, '//button[normalize-space()="For sale"]')
            ))
        else:
            for_sale_button = WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
                (By.XPATH, '//button[normalize-space()="For sale"]')
            ))
        do_wait(Wait.w_select)
        for_sale_button.click()
    except:
        print('ERROR @ get_webdriver(): No for sale button. Returning driver anyway')

    # If want to search sold houses as opposed to on-the-market houses
    # Less house value tables are available here. House value charts
    # are available, but I suspect these values are smoothed.
    # try:
    #     listing_type_button = WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
    #         (By.ID, 'listing-type')
    #     ))
    #     do_wait(Wait.w_select)
    #     listing_type_button.click()
    # except:
    #     print('ERROR @ get_webdriver(): No listing type button, no go. Returning None.')
    #     driver.close()
    #     return None
    # try:
    #     sold_button = WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
    #         (By.ID, 'isRecentlySold')
    #     ))
    #     do_wait(Wait.w_select)
    #     sold_button.click()
    #     form_done_button = WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
    #         (By.XPATH, '//button[normalize-space()="Done"]')
    #     ))
    #     do_wait(Wait.w_select)
    #     form_done_button.click()
    # except:
    #     print('ERROR @ get_webdriver(): Could not select "sold" listing type. Returning None.')
    #     driver.close()
    #     return None

    return driver

def try_get_table(driver, max_wait):
    try:
        # Zillow likes to block you here if you don't wait long enough
        table_view_button = WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
            (By.XPATH, '//button[normalize-space()="Table view"]')
        ))
        do_wait(Wait.w_select)
        driver.execute_script('arguments[0].click();', table_view_button)
        do_wait(Wait.w_select)
        return True
    except:
        print('WARNING @ search_county(): No table view available. Moving on.')
        return False

def try_close_lightbox(driver):
    do_wait(Wait.w_select)
    try:
        close_lightbox = driver.find_element_by_class_name('ds-close-lightbox-icon')
        driver.execute_script('arguments[0].click();', close_lightbox)
        return True
    except NoSuchElementException:
        print('no "x" for closing the lightbox. trying to wiggle out of this')
        try:
            click_away = driver.find_element_by_css_selector("div[class*='actionbar-inline srp-page-container tengage']")
            driver.execute_script('arguments[0].click();', click_away)
            return True
        except:
            return False

def record_home_data(county, driver, lock):
    months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]
    file_first_year = 2011
    file_start_index = 0
    do_wait(Wait.w_select)
    try:
        page_source = driver.page_source
        soup = bsoup(page_source, features='html.parser')

        address_chunk = soup.body.find('h1', attrs={'id': 'ds-chip-property-address'})
        address_spans = address_chunk.find_all('span', recursive=False)
        street_address = address_spans[0].text.strip(',')

        address_remainder = address_spans[1].text.strip()
        city_end_i =  address_remainder.find(',')
        city = address_remainder[:city_end_i].strip()
        state_zc = address_remainder[city_end_i+1:].split()
        state = state_zc[0]
        zc = state_zc[1]
    except Exception as e:
        print('ERROR @ record_home_data(): unable to get address data')
        print(e)
        return False

    try:
        zestimates = []
        # TODO: also check for exact dates (sales)
        # zsolds = []
        month_found_last_iter = False
        for td in soup.select('td[class*=StyledTableCell]'):
            td_text = td.get_text()
            includes_month_name = False
            for month in months:
                if month in td_text:
                    zestimates.append(td_text)
                    includes_month_name = True
                    month_found_last_iter = True
                    break
            if includes_month_name:
                continue
            if month_found_last_iter and '$' in td_text:
                # TODO: convert string dollar amts ($152.2K, $4.3M, etc) to no $'s or K/M's, thousands only
                td_text = td_text.strip('$')
                td_text_lower = td_text.lower()
                if 'k' in td_text_lower:
                    td_text_lower = float(td_text_lower.strip('k')) 
                elif 'm' in td_text_lower:
                    td_text_lower = float(td_text_lower.strip('m')) * 1000
                elif 'b' in td_text_lower:
                    td_text_lower = float(td_text_lower.strip('b')) * 1000000
                else:
                    # TODO: create error file to output whatever we get that we don't expect. Can then look up the property and figure out why
                    print(f'ERROR @ record_home_data(): {street_address}, {city}, {state} - no k, m, or b in house value string.')
                    return False
                zestimates.append(td_text_lower)
            month_found_last_iter = False
        if len(zestimates) > 0:
            zestimates = [
                (zestimates[i], zestimates[i+1]) 
                for i in range(len(zestimates)-2,-1,-2)
            ]
            first_month_yr = zestimates[0][0].split()
            first_month = first_month_yr[0]
            first_year = int(first_month_yr[1])
            j = months.index(first_month)
            yr_diff = first_year - file_first_year
            file_start_index = yr_diff * 12 - (8 - j)
        else:
            assert 1 == 0
    except Exception as e:
        print('ERROR @ record_home_data(): Unable to get price data')
        print(e)
        return False

    try:
        components_chunk = soup.body.find('span', attrs={'class': 'ds-bed-bath-living-area-container'})
        components_spans = components_chunk.find_all('span', recursive=True)
        beds = 'NA'
        baths = 'NA'
        sqft = 'NA'
        acres = 'NA'
        for span in components_spans:
            txt = span.text
            if 'bd' in txt:
                k = txt.split()
                try:
                    beds = int(k[0])
                except:
                    pass
            elif 'ba' in txt:
                k = txt.split()
                try:
                    baths = int(k[0])
                except:
                    pass
            elif 'sqft' in txt:
                k = txt.split()
                try:
                    sqft = int(k[0].replace(',', ''))
                except:
                    pass
            elif 'Acres' in txt:
                k = txt.split()
                try:
                    acres = float(k[0])
                except:
                    pass
    except Exception as e:
        print('ERROR @ record_home_data(): unable to get bed, bath, etc data')
        print(e)
        return False
        
    try:
        facts_and_features = soup.body.find_all('li', attrs={'class':"ds-home-fact-list-item"})
        fnf_type = 'NA'
        fnf_year_built = 'NA'
        fnf_heating = 'NA'
        fnf_cooling = 'NA'
        fnf_parking = 'NA'
        fnf_HOA = 'NA'
        fnf_lot = 'NA'
        for fnf in facts_and_features:
            feature_spans = fnf.find_all('span', recursive=False)
            feature_name = feature_spans[0].text.strip(':')
            feature_val = feature_spans[1].text
            if 'No Data' not in feature_val:
                try:
                    fnf_val = feature_val.split(',')
                    fnf_val = [item.strip(' ') + ',' for item in fnf_val]
                    fnf_val = [item.strip('|') for item in fnf_val]
                    fnf_val[-1] = fnf_val[-1][:-1]
                    fnf_val = ''.join(fnf_val)
                except:
                    fnf_val = feature_val
                if 'Type' in feature_name:
                    fnf_type = fnf_val
                elif 'Year built' in feature_name:
                    fnf_year_built = fnf_val
                elif 'Heating' in feature_name:
                    fnf_heating = fnf_val
                elif 'Cooling' in feature_name:
                    fnf_cooling = fnf_val
                elif 'Parking' in feature_name:
                    fnf_parking = fnf_val
                elif 'HOA' in feature_name:
                    fnf_HOA = fnf_val
                elif 'Lot' in feature_name:
                    fnf_lot = fnf_val
    except Exception as e:
        print('ERROR @ record_home_data(): unable to get fnf data')
        print(e)
        return False

    try:
        lock.acquire()
        try:
            with open('zest_data.csv', 'a') as data_file:
                data_file.write(
                    f'{county}|{street_address}|{city}|{state}|{zc}|{beds}|{baths}|{sqft}|{acres}|'  \
                    f'{fnf_type}|{fnf_year_built}|{fnf_heating}|{fnf_cooling}|{fnf_parking}|{fnf_HOA}|{fnf_lot}|'
                )
                price_i = 0
                price_str = ''
                while price_i < file_start_index:
                    price_str += 'NA|'
                    price_i += 1
                for price_item in zestimates:
                    price = price_item[1]
                    price_str += f'{price}|'
                    price_i += 1
                while price_i < 124:
                    price_str += 'NA|'
                    price_i += 1
                price_str = price_str[:-1] + '\n'
                data_file.write(price_str)
        finally:
            lock.release()
        return True
    except Exception as e:
        print('WARNING @ record_home_data(): unable to record home data')
        print(e)
        return False

def mouseover_properties(driver, properties, max_hover_ct):
    # hovering over a few random properties to mimic normal browsing
    try:
        hover_ct = random.randint(2, max_hover_ct)
        hover_props = random.sample(properties, hover_ct)
        for hover_prop in hover_props:
            ActionChains(driver).move_to_element(hover_prop).perform() 
            do_wait(Wait.w_mouseover)
    except StaleElementReferenceException:
        do_wait(Wait.w_select)

# if unfinished, return list of gathered addresses
def search_county(county, driver, prev_searched_addresses, lock, queue):
    max_wait = 40
    try:
        WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
            (By.CLASS_NAME, 'property-dot')
        ))
    except:
        return
    
    properties = driver.find_elements_by_class_name('property-dot')
    properties_ct = len(properties)
    county_short = county[:county.find('County')-1]

    if properties_ct > 2:
        cur_page = 0        
        for i in range(2):
            # Get the number of pages of property cards
            try:
                page_source = driver.page_source
                soup = bsoup(page_source, features='html.parser')
                page_ct_div = soup.body.find('div', attrs={'class':"search-pagination"})
                page_ct_inner_spans = page_ct_div.find_all('span', recursive=True)
                for span in page_ct_inner_spans:
                    txt = span.text
                    if 'Page' in txt:
                        k = txt.split(' ')
                        page_ct = int(k[-1])
            except:
                page_ct = 1

            # Iterate over all pages
            while cur_page < page_ct:
                cards = driver.find_elements_by_class_name('list-card')
                max_hover_ct = 7 if 7 < properties_ct else properties_ct
                searched_addresses = []

                try:
                    page_source = driver.page_source
                    soup = bsoup(page_source, features='html.parser')
                except:
                    print('ERROR @ search_county(): unable to collect addresses from cards.')
                # ... and all property cards
                for j in range(len(cards)):
                    # Must repopulate this list at least every few iterations while scrolling down
                    # because in the HTML, list indices are created but not populated til you scroll near it
                    cards = driver.find_elements_by_class_name('list-card')
                    card = cards[j]
                    mouseover_properties(driver, properties, max_hover_ct)
                    try:
                        driver.execute_script('arguments[0].scrollIntoView(true);', card)
                        do_wait(Wait.w_mouseover)
                        card_html = str(card.get_attribute('innerHTML'))
                        address_link_start = card_html.find('a href=') + 8
                        address_link_end = card_html[address_link_start:].find('"') + address_link_start
                        address_link = card_html[address_link_start:address_link_end]
                        address_text_end = address_link[:-1].rfind('/')
                        address_text_begin = address_link[:address_text_end].rfind('/') + 1
                        address = address_link[address_text_begin:address_text_end]
                        print(address)
                        if address in prev_searched_addresses:
                            continue
                        searched_addresses.append(address)
                    except:
                        print("ERROR @ search_county(): can't get address from card")
                        continue
                    try:
                        ActionChains(driver).move_to_element(card).perform() 
                        do_wait(Wait.w_mouseover)
                        driver.execute_script('arguments[0].click();', card)
                    except:
                        print("ERROR @ search_county(): couldn't click on property card")
                        continue
                    try:
                        get_table_success = try_get_table(driver, max_wait/2)
                        if get_table_success:
                            record_data_success = record_home_data(county_short, driver, lock)
                        try_close_lightbox(driver)
                    except:
                        # if something goes wrong, we're going to write error data, exit data and exit the process
                        print('ERROR @ search_county(): Process writing exit data and closing driver after error with table or lightbox.')
                        prev_searched_addresses.extend(searched_addresses)
                        lock.acquire()
                        try:
                            with open('error_counties.txt', 'a') as error_counties_f:
                                error_counties_f.write(f'{datetime.datetime.now().date()}: {county}\n')
                            write_partly_searched_county(county, prev_searched_addresses)
                        finally:
                            lock.release()
                        return
                    
                    # Checking if we got the signal to exit from user input; write exit data and exit the process
                    ret = queue.get()
                    if ret['exit'] == True:
                        queue.put(ret)
                        print('Process writing exit data and closing driver after requested exit.')
                        prev_searched_addresses.extend(searched_addresses)
                        lock.acquire()
                        try:
                            write_partly_searched_county(county, prev_searched_addresses)
                        finally:
                            lock.release()
                        return
                    queue.put(ret)

                if cur_page < page_ct - 1:
                    next_page_link = driver.find_element_by_xpath("//a[@title='Next page']")
                    do_wait(Wait.w_mouseover)
                    next_page_link.click()
                    do_wait(Wait.w_medium)
                cur_page += 1

            # Once we're done looking through agent listings, switch to other listings
            try:
                other_listings_button = driver.find_element_by_xpath('//button[text()="Other listings"]')
                ActionChains(driver).move_to_element(other_listings_button).perform() 
                do_wait(Wait.w_mouseover)
                driver.execute_script('arguments[0].click();', other_listings_button)
                do_wait(Wait.w_select)
            except:
                print('WARNING @ search_county(): no "other listings" button. Exiting county.')
                break
    else:
        print('not enough properties')
        
def write_partly_searched_county(county, searched_addresses):
    searched_addresses_ct = len(searched_addresses)
    try:
        assert searched_addresses_ct > 0
    except:
        print('ERROR: len 0 searched addresses list passed to write_party_searched_county()')
        return
    
    with open('partly_searched_temp.txt', 'a') as partly_searched_f:
        partly_searched_f.write(f'{county}:')
        for i in range(searched_addresses_ct - 1):
            address = searched_addresses[i]
            partly_searched_f.write(f'{address}||')
        partly_searched_f.write(f'{searched_addresses[searched_addresses_ct - 1]}\n')
    return

def wait_for_input_to_exit(queue):
    input()
    ret = queue.get()
    ret['exit'] = True
    queue.put(ret)

ret = {'exit': False}

if __name__ == '__main__':
    load_county_data()
    queue = Queue()
    queue.put(ret)
    output_lock = Lock()
    Process(target=wait_for_input_to_exit, args=(queue,)).start()

    options = webdriver.ChromeOptions()
    options.add_argument('disable-gpu')
    search_processes = []
    drivers = []

    f = open('partly_searched_temp.txt', 'w')
    f.close()

    for i in range(1):
        county_data, is_partly_searched = get_random_county()
        if is_partly_searched:
            county = county_data[0]
            prev_searched_addresses = county_data[1]
        else:
            county = county_data
            prev_searched_addresses = []
        driver = get_driver(county)
        drivers.append(driver)
        p = Process(target=search_county, args=(county, driver, prev_searched_addresses, output_lock, queue))
        p.start()
        p.join()
        search_processes.append(p)

    # while True:
    #     time.sleep(5)
    #     ret = queue.get()
    #     if ret['exit']:
    #         queue.put(ret)
    #         break
    #     queue.put(ret)
    #     for i in range(len(search_processes)):
    #         p = search_processes[i]
    #         if not p.is_alive():
    #             zc_data, is_partly_searched = get_random_zip()
    #             if is_partly_searched:
    #                 zc = zc_data[0]
    #                 prev_searched_addresses = zc_data[1]
    #             else:
    #                 zc = zc_data
    #                 prev_searched_addresses = []
    #             drivers[i] = get_driver(zc, drivers[i], True)
    #             search_processes[i] = Process(target=search_zip, args=(zc, drivers[i], prev_searched_addresses, output_lock, queue))
    #             search_processes[i].start()
    
    for driver in drivers:
        driver.close()
    rewrite_county_files_on_exit()
    print('Fin')