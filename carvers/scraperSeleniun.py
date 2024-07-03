import cloudscraper
import pandas as pd
import re
import logging
import time
import requests
import json

from PIL import Image
import io

from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import ProxyError, ConnectionError, Timeout

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import warnings


# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('proxy.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


MAX_WORKERS = 2
TIMEOUT = 3
MAX_RETRIES = 3
SCREENSHOT = True

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


"""
https://spys.me/proxy.txt
"""


# url = "https://www.proxynova.com/proxy-server-list/country-id/"

def selenium_scraper(url, type="text"):
    # Create a CloudScraper instance
    scraper = cloudscraper.create_scraper()

    # Set up the WebDriver (this example uses Chrome)
    driver_path = '/usr/bin/chromedriver'  # Replace with the actual path to your ChromeDriver
    service = Service(driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')  # Run Chrome in headless mode
    options.add_argument('--disable-gpu')  # Disable GPU acceleration (often necessary for headless mode)
    options.add_argument(f'user-agent={USER_AGENT}')


    # Open a CloudScraper session for proxy handling
    with scraper:
        # Use the session's proxy with Selenium
        driver_options = {
            # 'proxy': {
            #     'http': scraper.proxies['http'],
            #     'https': scraper.proxies['https'],
            #     'no_proxy': 'localhost,127.0.0.1'  # Exclude local addresses from proxying
            # }
        }

        # Initialize WebDriver with options
        # driver = webdriver.Chrome(service=service, options=options, seleniumwire_options=driver_options)
        driver = webdriver.Chrome(service=service, options=options)

        try:
            # Open the URL
            driver.get(url)
            time.sleep(1)  # Adjust the sleep time based on your internet speed


            if type == "json":
                content = driver.page_source
                content = driver.find_element(By.TAG_NAME, 'pre').text
                return json.loads(content)

            # do screenCapture
            if type == "image":    
                screenshot_as_png = driver.get_screenshot_as_png()

                # Convertir la capture d'écran en image PIL
                image = Image.open(io.BytesIO(screenshot_as_png))

                # Enregistrer l'image en tant que fichier JPEG
                name = url.split('/')[-3]
                image.save(f'{name}.jpeg', 'JPEG')

            # Get the page HTML
            page_html = driver.page_source
            return page_html

        finally:
            # Close the WebDriver
            driver.quit()


def test_proxy(proxy_tuple, url_to_check='http://www.example.com', max_retries=MAX_RETRIES):
    ip, port = proxy_tuple[:2]  # Extract IP and Port from the tuple
    proxy_url = f'http://{ip}:{port}'  # Use HTTP proxy URL

    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }

    for attempt in range(max_retries):
        try:
            logger.info(f"{proxy_url}")
            response = requests.get(url_to_check, proxies=proxies, timeout=TIMEOUT)
            if response.status_code == 200:
                return True
        except (ProxyError, ConnectionError, Timeout) as e:
            logger.error(f"Error testing proxy {proxy_tuple}: {str(e)}")
            continue  # Retry if there's an error like ProxyError, ConnectionError or Timeout
        except Exception as e:
            logger.error(f"Unknown error testing proxy {proxy_tuple}: {str(e)}")
    return False

def spys_one_proxy():
    url = "https://spys.one/en/anonymous-proxy-list/"
    scraper = cloudscraper.create_scraper()
    logger.info(f"{url}")
    response = scraper.get(url)
    df = pd.read_html(response.text)[2]


def spys_me_proxy():
    """
    https://spys.me/proxy.txt
    """
    url = "https://spys.me/proxy.txt"
    scraper = cloudscraper.create_scraper()
    logger.info(f"{url}")
    response = scraper.get(url)
    proxy_pattern = r'(\d+\.\d+\.\d+\.\d+):(\d+)\s+\w{2}-[A-Z!+-]+\s+-\s+'
    proxies_list = re.findall(proxy_pattern, response.text)
    return proxies_list

def free_proxy_list():
    scraper = cloudscraper.create_scraper()
    response = scraper.get("https://free-proxy-list.net/")
    df = pd.read_html(response.text)[0]
    list = [tuple(x) for x in df.to_numpy()]
    return list


def validate_proxy_list(proxies_list):
    with warnings.catch_warnings(action="ignore"):
        print("len : ", len(proxies_list))
        # Test proxies asynchronously
        working_proxies = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(test_proxy, proxy) for proxy in proxies_list]
            
            for future in as_completed(futures):
                if future.result():
                    working_proxies.append(future.args[0])  # Append the tuple that was tested

        # Print or use the list of working proxies
        # print("Working proxies:")
        # for proxy in working_proxies:
        #     print(proxy)
        return working_proxies
    


# url = "https://www.tf1.fr"
# url = "https://spys.one/en/anonymous-proxy-list/"
# html_content = selenium_scraper(url=url)
# dataframe = pd.read_html(html_content)
# print(dataframe)