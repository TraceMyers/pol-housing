from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN 
# from multiprocessing import Pool, Process, Manager 
# import requests
from bs4 import BeautifulSoup
import time
import random
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

def new_random_connection():
    dots_len = 0
    attempts = 0
    dots = []

    while dots_len == 0 and attempts < max_attempts:
        go_to_next_iter = False
        try:
            # rotate_VPN()
            time.sleep(3)
            driver.get('http://www.zillow.com')
            search_box = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
                (By.XPATH, '//input[@type="text"]')
            ))
            time.sleep(random.randint(2,5))
            driver.execute_script('arguments[0].click();', search_box)
            zip_code = str(random.choice(zip_codes))
            time.sleep(random.random() * 8)
            for digit in zip_code:
                search_box.send_keys(digit)
                time.sleep(random.random() / 4)
            time.sleep(random.random() / 5)
            search_box.send_keys(Keys.RETURN)

            # TODO: sometimes this lightbox doesn't show up, so need to probably break up these try/excepts
            for_sale_button = WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable(
               (By.XPATH, '//button[normalize-space()="For sale"]')
            ))
            print(for_sale_button)
            time.sleep(random.random() * 2 + 0.2)
            for_sale_button.click()

            # WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'property-dot')))
            time.sleep(5)
        except TimeoutException:
            print('failed to connect to url')
            go_to_next_iter = True
        except WebDriverException as e:
            print('Some driver error')
            print(e)
            go_to_next_iter = True
        except ConnectionAbortedError:
            print('connection was aborted by host machine (?) Trying again')
            go_to_next_iter = True

        if not go_to_next_iter:
            dots = driver.find_elements_by_class_name('property-dot')
            dots_len = len(dots)
        attempts += 1
    
    if attempts == max_attempts:
        print(f'failed after {max_attempts} attempts. aborting execution')
        exit()
    return dots, dots_len

# TODO: create a random set of actions that can be performed while browsing (clicking, scrolling, waiting, etc.)
# TODO: something like this (but jesus the cost) https://oxylabs.io/pricing/residential-proxy-pool
# but only after doing a decent job of getting a single process to collect data
# probably use free proxies to test multiprocess until ready to scale up 
# TODO: might get a small 'verify you're human to continue' lightbox when clicking on a dot. I think
# you can get past it by clicking outside the box? (attempt in code already)
# TODO: probably implement a slightly randomized time limit for each process
# TODO: research the traffic time distribution of zillow so scaping isn't happening at weird hours
# TODO: try entering a city/county/whatever through the front page of zillow. Most people do that.
# TODO: sometimes clicking on a property doesn't open the normal lightbox, and instead just has a 
#       button in the upper left that says 'Back to search' (not sure on capitalization); might
#       be window width dependent - don't know, just got it once. need to control for this

# NOTE: Zillow might adapt its anti-automating tech to meet this bot while it's collecting data,
# so I need the bot to be prepared for things that it's not currently getting caught for now;
# it should be essentially impossible to tell this bot from a person
# NOTE: selecting an apartment gives a different lightbox interface
# NOTE: some homes are similar to apartments in that they may have multiple realty listings inside one lightbox
# NOTE: make number of processes scale up over a long-ish time frame so that new users doesn't spike.

# options = webdriver.ChromeOptions()
# options.add_argument('--ignore-certificate-errors')
# options.add_argument('--incognito')
# options.add_argument('--headless')
driver = webdriver.Chrome()

# initialize_VPN(save=1,area_input=['United States'])
n = 3
dot_i = 0

max_wait = 15
max_attempts = 10

zip_code_df = pd.read_csv('us_zip_codes/uszips.csv')
high_population = zip_code_df.loc[zip_code_df['population'] >= 100] # 100 is the 5th percentile cutoff
zip_codes = list(high_population['zip'])


dots, dots_len = new_random_connection()
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

while True:
    finished_dots = True
    for dot in dots:
        wait = random.randint(10, 18)
        print(f'waiting {wait} seconds')
        time.sleep(wait)

        # hovering appears to help; otherwise it often says there was an issue loading
        # and it provides a link to a captcha

        hover_ct = random.randint(3, 10)
        for i in range(hover_ct):
            random_hover_dot = dots[random.randint(0, dots_len - 1)]
            ActionChains(driver).move_to_element(random_hover_dot).perform() 
            wait = random.random() * 0.5 + 0.1
            print(f'waiting {wait} seconds')
            time.sleep(wait)

        ActionChains(driver).move_to_element(dot).perform() 
        wait = random.random() * 3 + 0.5
        print(f'waiting {wait} seconds')
        time.sleep(wait)

        driver.execute_script('arguments[0].click();', dot)
        # page_source = driver.page_source
        # soup = BeautifulSoup(page_source, features='html.parser')

        wait = random.randint(15, 30)
        print(f'waiting {wait} seconds')
        time.sleep(wait)

        try:
            # TODO: wait until can see text
            # WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'property-dot')))
            table_view_button = driver.find_element_by_xpath('//button[normalize-space()="Table view"]')
            driver.execute_script('arguments[0].click();', table_view_button)

            # TODO: wait until can see table
            # WebDriverWait(driver, max_wait).until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'property-dot')))
            wait = random.randint(5, 9)
            print(f'waiting {wait} seconds')
            time.sleep(wait)

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, features='html.parser')
            td_list = []
            for td in soup.select('td[class*=StyledTableCell]'):
                td_text = td.get_text()
                includes_month_name = False
                for month in months:
                    if month in td_text:
                        td_list.append(td_text)
                        includes_month_name = True
                        break
                if not includes_month_name and '$' in td_text:
                    td_list.append(td_text)
            for item in td_list:
                print(item)
            # print('got page info')
        except WebDriverException:
            print('Some driver error')
        except NoSuchElementException:
            print("can't find 'table view' button. trying to close the lightbox")

        wait = random.randint(2, 5)
        print(f'waiting {wait} seconds')
        time.sleep(wait)

        # TODO: close the table lightbox
        # class includes "CloseButton"

        try:
            close_lightbox = driver.find_element_by_class_name('ds-close-lightbox-icon')
            driver.execute_script('arguments[0].click();', close_lightbox)
        except NoSuchElementException:
            print('no "x" for closing the lightbox. trying to wiggle out of this')
            try:
                click_away = driver.find_element_by_css_selector("div[class*='actionbar-inline srp-page-container tengage']")
                driver.execute_script('arguments[0].click();', click_away)
            except:
                finished_dots = False
                break

    continue_execution = True
    while True:
        ans = input(f'finished dots: {"true" if finished_dots else "false"}. continue (y/n)?')
        if 'n' in ans:
            continue_execution = False
            break
        elif not 'y' in ans:
            print('please type anything with a "y" or "n" in it and hit enter to answer')
        else:
            break
    if not continue_execution:
        break
    dots, dots_len = new_random_connection()


# try:
#     myElem = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.ID, 'IdOfMyElement')))
#     print "Page is ready!"
# except TimeoutException:
#     print "Loading took too much time!"



# terminate_VPN(instructions)

# def f(process_list):
#     for i in range(5):
#         process_list.append(i)

# if __name__ == '__main__':
#     with Manager() as manager:
#         process_list = manager.list()
#         processes = [Process(target=f, args=(process_list,)) for i in range(5)]
#         for p in processes:
#             p.start()
#             p.join()
#         for p in processes:
#             p.terminate()
#         print(process_list)

#div class="property-dot"
#https://www.zillow.com/clay-county-fl/sold/

# url = 'https://www.zillow.com/clay-county-fl/sold/'
# headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
# page = requests.get(url, headers=headers)
# soup = bsoup(page.content, 'html.parser')

# tags = soup.find_all(class_="property-dot")
#https://github.com/ChrisMuir/Zillow/blob/master/zillow_functions.py
# print(tags)
# for tag in tags:
#     for i in soup.find_all(tag):
#         print(type(i))
#         if i is not None and i.has_attr('class'):
#             if len(i['class']) != 0 and 'property-dot' in i['class']:
#                 print('found dot')

#https://github.com/ChrisMuir/Zillow/blob/master/zillow_functions.py