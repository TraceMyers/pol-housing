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

import http.client
import socket
from selenium import webdriver
from selenium.webdriver.remote.command import Command 
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
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.action_chains import ActionChains

from multiprocessing.dummy import Process, Lock, Queue

# TODO function for error/success reporting including area name
# less printing, only print when something important happens

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
        self.mouseover_waits.iloc[self.mouseover_waits < 0.01] = 0.05
        self.mouseover_waits = np.array(self.mouseover_waits)
        self.mwaits_i = 0

        self.select_wait_mean = 1.0
        self.select_wait_sd = 0.4
        self.select_waits = pd.DataFrame(np.random.normal(
            self.select_wait_mean,
            self.select_wait_sd,
            self.waits_n
        ))
        self.select_waits.iloc[self.mouseover_waits < 0.1] = 0.4
        self.select_waits = np.array(self.select_waits)
        self.swaits_i = 0

        self.typekeys_wait_mean = 0.09
        self.typekeys_wait_sd = 0.06
        self.typekeys_waits = pd.DataFrame(np.random.normal(
            self.typekeys_wait_mean,
            self.typekeys_wait_sd,
            self.waits_n
        ))
        self.typekeys_waits.iloc[self.typekeys_waits < 0.03] = 0.04
        self.typekeys_waits = np.array(self.typekeys_waits)
        self.typekeys_i = 0

        self.long_wait_mean = 13
        self.long_wait_sd = 5
        self.long_waits = pd.DataFrame(np.random.normal(
            self.long_wait_mean,
            self.long_wait_sd,
            self.waits_n
        ))
        self.long_waits.iloc[self.long_waits < 10] = 9
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

class AreaData:
    def __init__(self):
        self.unsearched = []
        self.partly_searched = []

    def load(self):
        with open('unsearched_areas.txt', 'r') as unsearched_f:
            for line in unsearched_f:
                self.unsearched.append(line.strip('\n'))
        
        with open('partly_searched_areas.txt', 'r') as partly_f:
            for line in partly_f:
                colon_i = line.find(':')
                area = line[:colon_i]
                addresses = line[colon_i+1:].split('||')
                addresses[-1] = addresses[-1].strip('\n')
                self.partly_searched.append((area, addresses))

    def get_random_area(self):
        partly_searched_ct = len(self.partly_searched)
        unsearched_ct = len(self.unsearched)
        if partly_searched_ct > 0:
            pick_searched = random.choice([0,1])
            if pick_searched or unsearched_ct < 1:
                selected_area_i = random.randint(0,partly_searched_ct-1)
                ps_area_data = self.partly_searched[selected_area_i]
                self.partly_searched.pop(selected_area_i)
                return ps_area_data, True
        selected_area_i = random.randint(0, unsearched_ct-1)
        area = self.unsearched[selected_area_i]
        self.unsearched.pop(selected_area_i)
        return area, False

    def rewrite_area_files_on_exit(self):
        for ps in self.partly_searched:
            write_partly_searched_area(ps[0], ps[1])
        os.remove('partly_searched_areas.txt')
        os.rename('partly_searched_temp.txt', 'partly_searched_areas.txt')
        unsearched_len = len(self.unsearched)
        if unsearched_len > 0:
            with open('unsearched_areas.txt', 'w') as unsearched_f:
                if unsearched_len > 1:
                    for i in range(len(self.unsearched) - 1):
                        unsearched_f.write(f'{self.unsearched[i]}\n')
                unsearched_f.write(f'{self.unsearched[-1]}')

class AccountDispenser:
    def __init__(self):
        self.usernames = []
        self.passwords = []
        self.acct_ctr = 0
        self.account_ct = 6
        i = 0
        with open('account_stuff/account_names.txt', 'r') as acf:
            for line in acf:
                username_end = line.rfind(',')
                username_begin = line[:username_end].rfind(',') + 1
                username = line[username_begin:username_end]
                password = line[username_end+1:-1]
                self.usernames.append(username)
                self.passwords.append(password)
                i += 1
                if i == self.account_ct:
                    break
    
    def get_user_pass(self):
        user = self.usernames[self.acct_ctr]
        pwd = self.passwords[self.acct_ctr]
        self.acct_ctr += 1
        if self.acct_ctr == self.account_ct:
            self.acct_ctr = 0
        return user, pwd
            

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

def is_alive(driver):
    try:
        driver.execute(Command.STATUS)
        return True
    except (socket.error, http.client.CannotSendRequest):
        return False

# remember to close driver on exit or before getting a new one
max_wait = 30
def get_driver(area, user_pass=None, driver=None, short_wait=False):
    if driver is None:
        driver = webdriver.Chrome()
    driver.get('http://www.zillow.com')
    # if user_pass is not None:
    #     try:
    #         do_wait(Wait.w_select)
    #         sign_in_link = WebDriverWait(driver, max_wait).until(expected_conditions.presence_of_element_located(
    #             (By.PARTIAL_LINK_TEXT, 'Sign in')
    #         ))
    #         driver.execute_script('arguments[0].click();', sign_in_link)
    #         print(sign_in_link)

    #         do_wait(Wait.w_medium)
    #         google_btn = driver.find_element_by_xpath('//button[text()="Continue with Google"]')
    #         print(google_btn)
    #         driver.execute_script('arguments[0].click();', google_btn)

    #         do_wait(Wait.w_medium)
    #         print(driver.window_handles)
    #         driver.switch_to_window(driver.window_handles[1])

    #         email_box = WebDriverWait(driver, max_wait).until(expected_conditions.presence_of_element_located(
    #             (By.XPATH, '//input[@type="email"]')
    #         ))
    #         driver.execute_script('arguments[0].click();', email_box)
    #         do_wait(Wait.w_select)
    #         for c in user_pass[0]:
    #             email_box.send_keys(c)
    #             do_wait(Wait.w_typekeys)
    #         do_wait(Wait.w_typekeys)
    #         email_box.send_keys(Keys.RETURN)
    #         input('hit enter when done logging in')
            
    #         driver.switch_to_window(driver.window_handles[0])
    #     except:
    #         print('ERROR @ get_driver(): login failed returning')
    #         return
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
        for c in area:
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
        table_view_button = WebDriverWait(driver, max_wait *0.6).until(expected_conditions.element_to_be_clickable(
            (By.XPATH, '//button[normalize-space()="Table view"]')
        ))
        do_wait(Wait.w_select)
        driver.execute_script('arguments[0].click();', table_view_button)
        return True
    except:
        print('WARNING @ search_area(): No table view available. Moving on.')
        return False

def try_close_lightbox(driver):
    do_wait(Wait.w_mouseover)
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

def record_home_data(area, address_head, driver, lock):
    months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]
    file_first_year = 2011
    file_start_index = 0
    do_wait(Wait.w_select)

    page_source = driver.page_source
    soup = bsoup(page_source, features='html.parser')

    ds_chip_address_id = False
    try:
        address_chunk = soup.body.find('h1', attrs={'id': 'ds-chip-property-address'})
        address_spans = address_chunk.find_all('span', recursive=False)
        street_address = address_spans[0].text.strip(',')

        address_remainder = address_spans[1].text.strip()
        city_end_i =  address_remainder.find(',')
        city = address_remainder[:city_end_i].strip()
        state_zc = address_remainder[city_end_i+1:].split()
        state = state_zc[0]
        zc = state_zc[1]
    except:
        ds_chip_address_id = False
    
    if not ds_chip_address_id and address_head is not None:
        try:
            elements = soup.body.find_all('h1', recursive=True)
            for element in elements:
                txt = element.text
                if address_head in txt:
                    street_address_end = txt.find(',')
                    city_end = txt[street_address_end+1:].find(',') + street_address_end + 1
                    state_zip = txt[city_end+1:].strip(' ').split(' ')

                    street_address = txt[:street_address_end]
                    city = txt[street_address_end+1:city_end].strip()
                    state = state_zip[0]
                    zc = state_zip[1]
                    break
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
        ds_bed_bath_container = True
        try:
            components_chunk = soup.body.find('span', attrs={'class': 'ds-bed-bath-living-area-container'})
            components_spans = components_chunk.find_all('span', recursive=True)
        except:
            ds_bed_bath_container = False
        if not ds_bed_bath_container:
            components_chunk = soup.body.find('ul', attrs={'class': 'ds-home-fact-list'})
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
                    f'{area}|{street_address}|{city}|{state}|{zc}|{beds}|{baths}|{sqft}|{acres}|'  \
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
def search_area(area, driver, prev_searched_addresses, lock, queue):
    max_wait = 40
    try:
        WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
            (By.CLASS_NAME, 'property-dot')
        ))
    except:
        return
    
    properties = driver.find_elements_by_class_name('property-dot')
    properties_ct = len(properties)
    area_short = area[:area.find('County')-1]

    searched_addresses = []
    if properties_ct > 2:
        for i in range(2):
            cur_page = 0        
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
                successive_failures = 0

                # ... and all property cards
                for j in range(len(cards)):
                    # Must repopulate this list at least every few iterations while scrolling down
                    # because in the HTML, list indices are created but not populated til you scroll near it
                    driver_alive = True
                    if not is_alive(driver):
                        do_wait(Wait.w_long)
                        if not is_alive(driver):
                            driver_alive = False
                    if successive_failures == 2 or not driver_alive:
                        print("ERROR @ search_area(): Exiting search after 2 successive failures.")
                        prev_searched_addresses.extend(searched_addresses)
                        lock.acquire()
                        try:
                            with open('error_areas.txt', 'a') as error_areas_f:
                                error_areas_f.write(f'{datetime.datetime.now().date()}: {area}\n')
                            ret = queue.get()
                            partly_searched = ret['partly_searched']
                            partly_searched.append((area, prev_searched_addresses))
                            queue.put(ret)
                        finally:
                            lock.release()
                        return
                    try:
                        WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
                            (By.CLASS_NAME, 'list-card')
                        ))
                        cards = driver.find_elements_by_class_name('list-card')
                        card = cards[j]
                    except:
                        print("ERROR @ search_areas(): can't grab list card")
                    
                    address_head = None
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

                        address_head = address[:10].replace('-', ' ')

                        print(address)
                        if address in prev_searched_addresses:
                            continue
                        searched_addresses.append(address)
                    except:
                        print("ERROR @ search_area(): can't get address from card")
                    try:
                        mouseover_properties(driver, properties, max_hover_ct)
                        ActionChains(driver).move_to_element(card).perform() 
                        driver.execute_script('arguments[0].click();', card)
                    except:
                        print("ERROR @ search_area(): couldn't click on property card")
                    try:
                        get_table_success = try_get_table(driver, max_wait)
                        record_data_success = record_home_data(area_short, address_head, driver, lock)
                        lightbox_close_success = try_close_lightbox(driver)
                        
                        if not lightbox_close_success:
                            successive_failures += 1
                        else:
                            successive_failures = 0
                    except:
                        # if something goes wrong, we're going to write error data, exit data and exit the process
                        print('ERROR @ search_area(): error with table or lightbox.')
                        successive_failures += 1
                    
                    # Checking if we got the signal to exit from user input; write exit data and exit the process
                    lock.acquire()
                    ret = queue.get()
                    if ret['exit'] == True:
                        print('Process writing exit data and closing driver after requested exit.')
                        prev_searched_addresses.extend(searched_addresses)
                        partly_searched = ret['partly_searched']
                        partly_searched.append((area, prev_searched_addresses))
                        queue.put(ret)
                        lock.release()
                        return
                    queue.put(ret)
                    lock.release()

                if cur_page < page_ct - 1:
                    next_page_link = driver.find_element_by_xpath("//a[@title='Next page']")
                    do_wait(Wait.w_mouseover)
                    driver.execute_script('arguments[0].click();', next_page_link)
                    do_wait(Wait.w_medium)
                cur_page += 1

            # Once we're done looking through agent listings, switch to other listings
            try:
                other_listings_button = driver.find_element_by_xpath('//button[text()="Other listings"]')
                ActionChains(driver).move_to_element(other_listings_button).perform() 
                do_wait(Wait.w_mouseover)
                driver.execute_script('arguments[0].click();', other_listings_button)
                do_wait(Wait.w_medium)
            except:
                print('WARNING @ search_area(): no "other listings" button. Exiting area.')
                break
    else:
        print('not enough properties')
    lock.acquire()
    try:
        with open('finished_areas.txt', 'a') as fc_f:
            fc_f.write(f"{area}\n")
    finally:
        lock.release()
    
        
def write_partly_searched_area(area, searched_addresses):
    searched_addresses_ct = len(searched_addresses)
    with open('partly_searched_temp.txt', 'a') as partly_searched_f:
        partly_searched_f.write(f'{area}:')
        for i in range(searched_addresses_ct - 1):
            address = searched_addresses[i]
            partly_searched_f.write(f'{address}||')
        partly_searched_f.write(f'{searched_addresses[searched_addresses_ct - 1]}\n')
    return

def wait_for_input_to_exit(queue, lock):
    input()
    lock.acquire()
    ret = queue.get()
    ret['exit'] = True
    queue.put(ret)
    lock.release()

ret = {'exit': False}

if __name__ == '__main__':
    area_data = CountyData()
    area_data.load()
    queue = Queue()
    queue.put(ret)
    output_lock = Lock()
    ret['partly_searched'] = area_data.partly_searched

    options = webdriver.ChromeOptions()
    options.add_argument('disable-gpu')
    search_processes = []
    drivers = []

    accounts = AccountDispenser()

    f = open('partly_searched_temp.txt', 'w')
    f.close()

    driver_ct = 1

    for i in range(driver_ct):
        cnty_data, is_partly_searched = area_data.get_random_area()
        if is_partly_searched:
            area = cnty_data[0]
            prev_searched_addresses = cnty_data[1]
        else:
            area = cnty_data
            prev_searched_addresses = []
        user_pass = accounts.get_user_pass()
        driver = get_driver(area, user_pass)
        drivers.append(driver)
        p = Process(target=search_area, args=(area, driver, prev_searched_addresses, output_lock, queue))
        p.start()
        search_processes.append(p)

    Process(target=wait_for_input_to_exit, args=(queue,output_lock)).start()
    while True:
        time.sleep(5)
        output_lock.acquire()
        ret = queue.get()
        if ret['exit']:
            queue.put(ret)
            output_lock.release()
            break
        queue.put(ret)
        output_lock.release()
        for i in range(len(search_processes)):
            p = search_processes[i]
            if not p.is_alive():
                cnty_data, is_partly_searched = area_data.get_random_area()
                if is_partly_searched:
                    area = cnty_data[0]
                    prev_searched_addresses = cnty_data[1]
                else:
                    area = cnty_data
                    prev_searched_addresses = []
                try:
                    drivers[i] = get_driver(area, None, drivers[i], True)
                except (NoSuchWindowException, WebDriverException):
                    try:
                        drivers[i].close()
                    except:
                        pass
                    drivers[i] = get_driver(area)
                search_processes[i] = Process(target=search_area, args=(area, drivers[i], prev_searched_addresses, output_lock, queue))
                search_processes[i].start()
    
    for driver in drivers:
        try:
            driver.close()
        except:
            pass
    input('Press enter once all windows are closed')
    area_data.rewrite_area_files_on_exit()
    print('Fin')