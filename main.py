from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN 
from multiprocessing import Pool, Process, Manager 
import requests
from bs4 import BeautifulSoup as bsoup
import time


# instructions = initialize_VPN(area_input=['complete rotation'])
# r = 1

# for i in range(r):
#     rotate_VPN(instructions)
#     print('doing things')
#     time.sleep(10)

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

url = 'https://www.zillow.com/clay-county-fl/sold/'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
page = requests.get(url, headers=headers)
soup = bsoup(page.content, 'html.parser')

tags = soup.find_all(class_="property-dot")
#https://github.com/ChrisMuir/Zillow/blob/master/zillow_functions.py
print(tags)
# for tag in tags:
#     for i in soup.find_all(tag):
#         print(type(i))
#         if i is not None and i.has_attr('class'):
#             if len(i['class']) != 0 and 'property-dot' in i['class']:
#                 print('found dot')

# need to switch to selenium

#https://github.com/ChrisMuir/Zillow/blob/master/zillow_functions.py