import os
import zlib
import time
import queue
import logging
import threading
import requests
import sqlite3
import random
import cloudscraper
import hashlib
import ssdeep
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.0.0 Safari/537.36"


# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('proxy.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Définition des sources de proxy
proxy_list_urls = {
    "sock5": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "sock4": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
    "http": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "proxyscape": "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text",
    "spys": "https://spys.me/proxy.txt"
}

class Proxy:
    TIMEOUT = 3
    DELAY = 0.3  # delay 1
    CACHE_EXPIRY_HOURS = 24
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'android',
            'custom': USER_AGENT,
            'desktop': False
        }
    )
    doclean = False

    def __init__(self, proxy_on=False, timeout: int = TIMEOUT, caching=True) -> None:
        self.proxy_on = proxy_on
        self.caching = caching
        logger.info("Initializing proxy manager")
        self.timeout = timeout
        self.proxy_queue = queue.Queue()
        self.conn = sqlite3.connect('proxies.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()
        self._create_proxy_table()
        self._create_cache_table()

    def _create_proxy_table(self):
        with self.lock:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS proxies
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proxy TEXT UNIQUE)''')
            self.conn.commit()

    def _create_cache_table(self):
        with self.lock:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS cache
                        (url TEXT PRIMARY KEY,
                        content BLOB,
                        timestamp DATETIME,
                        md5 TEXT,
                        ssdeep TEXT)''')
            self.conn.commit()

    def delete_old_cache_entries(self, days=777):
        threshold_date = datetime.now() - timedelta(days=days)
        with self.lock:
            self.cursor.execute("DELETE FROM cache WHERE timestamp < ?", (threshold_date,))
            self.conn.commit()
            logger.info(f"Deleted cache entries older than {days} days")

    def clean(self, conn, cursor):
        url = "http://www.example.com"
        logger.info("start clean")
        logger.info(f" doclean status : {self.doclean}")
        while self.doclean:
            proxy = self._get_random_proxy(cursor)
            if not proxy:
                logger.warning("No more proxy available.")
                break
            proxies = {'http': proxy, 'https': proxy}
            logger.info(f"proxy : {proxies}")

            try:
                response = self.scraper.get(url, proxies=proxies, timeout=self.TIMEOUT)
                if response.status_code == 407:
                    raise requests.HTTPError('Proxy Authentication Required (407)')
                # logger.info(f"Request successful using proxy: {proxy}")
            except requests.RequestException as e:
                logger.error(f"Request failed with proxy {proxy}: {e}")
                cursor.execute("DELETE FROM proxies WHERE proxy = ?", (proxy,))
                conn.commit()

    def _get_random_proxy(self, cursor):
        cursor.execute("SELECT proxy FROM proxies ORDER BY RANDOM() LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None

    def start_cleaning(self):
        def run_cleaning():
            try:
                with sqlite3.connect('proxies.db', check_same_thread=False) as conn:
                    cursor = conn.cursor()
                    self.clean(conn, cursor)
            except Exception as e:
                logger.error(f"Exception in cleaning thread: {e}", exc_info=True)

        try:
            self.doclean = True
            self.cleaning_thread = threading.Thread(target=run_cleaning)
            self.cleaning_thread.start()
        except Exception as e:
            logger.error(f"Failed to start cleaning thread: {e}")

    def stop_cleaning(self):
        self.doclean = False
        if self.cleaning_thread.is_alive():
            self.cleaning_thread.join()

    def _remove_failed_proxies(self):
        while not self.proxy_queue.empty():
            proxy = self.proxy_queue.get()
            with self.lock:
                self.cursor.execute("DELETE FROM proxies WHERE proxy = ?", (proxy,))
                self.conn.commit()

    def close(self):
        self.conn.close()
        logger.info("Database connection closed")

    def _is_proxylist_empty(self):
        with self.lock:
            self.cursor.execute("SELECT COUNT(*) FROM proxies;")
            record_count = self.cursor.fetchone()[0]
        # Check if the list of proxies is empty
        if record_count == 0:
            logger.info("Proxy list is empty")
            return True
        else:
            return False

    def _download_proxy_list(self):
        """
        Download proxy list
        """
        with self.lock:
            for key, url in proxy_list_urls.items():
                response = self.scraper.get(url)
                proxy_list = response.text.strip().split('\n')
                for proxy in proxy_list:
                    proxy = proxy.replace("\r", "")
                    if key != "proxyscape":
                        proxy = f"{key}://{proxy}"
                    self.cursor.execute("INSERT OR IGNORE INTO proxies (proxy) VALUES (?)", (proxy,))
            self.conn.commit()
            logger.info("Updated Proxy List")

    def _get_cached_content(self, url: str) -> tuple[bytes, str, str]:
        with self.lock:
            self.cursor.execute("SELECT content, timestamp, md5, ssdeep FROM cache WHERE url = ?", (url,))
            result = self.cursor.fetchone()
        if result:
            compressed_content, timestamp, md5, ssdeep = result
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            if datetime.now() - timestamp < timedelta(hours=self.CACHE_EXPIRY_HOURS):
                return self.decompress_string(compressed_content), md5, ssdeep
        return None, None, None

    def _cache_content(self, url: str, content: bytes):
        timestamp = datetime.now()
        compressed_content = self.compress_string(content)
        md5_hash = self.compute_md5(content)
        ssdeep_hash = self.compute_ssdeep(content)
        with self.lock:
            self.cursor.execute("INSERT OR REPLACE INTO cache (url, content, timestamp, md5, ssdeep) VALUES (?, ?, ?, ?, ?)",
                                (url, compressed_content, timestamp, md5_hash, ssdeep_hash))
            self.conn.commit()

    def compute_md5(self, content: bytes) -> str:
        return hashlib.md5(content).hexdigest()
    
    def compute_ssdeep(self, content: bytes) -> str:
        return ssdeep.hash(content)

    def _process_and_cache_content(self, url: str, content: bytes, cached_md5_hash: str, cached_ssdeep_hash: str):
        """
        Process the content by computing hashes and caching it.

        :param url: The URL of the content.
        :param content: The content to process.
        :param cached_md5_hash: The cached MD5 hash.
        :param cached_ssdeep_hash: The cached SSDEEP hash.
        """
        md5_hash = self.compute_md5(content)
        ssdeep_hash = self.compute_ssdeep(content)

        logger.info(f"MD5: {md5_hash}")
        logger.info(f"SSDEEP: {ssdeep_hash}")

        # Optionally, compare with existing hashes if needed before caching
        if cached_md5_hash and cached_ssdeep_hash:
            if md5_hash == cached_md5_hash and ssdeep.compare(ssdeep_hash, cached_ssdeep_hash) == 100:
                logger.info("Content has not changed")
                return

        self._cache_content(url, content)

    def _test_proxy(self):
        try:
            with sqlite3.connect('proxies.db', check_same_thread=False) as conn:
                cursor = conn.cursor()
                url = "http://www.example.com"
            logger.info("start clean")
            logger.info(f" doclean status : {self.doclean}")
            while self.doclean:
                proxy = self._get_random_proxy(cursor)
                if not proxy:
                    logger.warning("No more proxy available.")
                    break
                proxies = {'http': proxy, 'https': proxy}
                logger.info(f"proxy : {proxies}")

                try:
                    response = self.scraper.get(url, proxies=proxies, timeout=self.TIMEOUT)
                    if response.status_code == 407:
                        raise requests.HTTPError('Proxy Authentication Required (407)')
                    logger.info(f"Request successful using proxy: {proxy}")
                except requests.RequestException as e:
                    cursor.execute("DELETE FROM proxies WHERE proxy = ?", (proxy,))
                    conn.commit()

        except Exception as e:
            logger.error(f"Exception in cleaning thread: {e}", exc_info=True)

    def test_proxies(self, max_workers=100):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._test_proxy) for _ in range(max_workers)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Exception during proxy testing: {e}", exc_info=True)

    def compress_string(self, input_string: bytes) -> bytes:
        """
        Compress a byte string using zlib.

        :param input_string: The byte string to compress.
        :return: The compressed data as bytes.
        """
        return zlib.compress(input_string)
  
    def decompress_string(self, compressed_data: bytes) -> bytes:
        """
        Decompress a zlib-compressed byte string.

        :param compressed_data: The compressed data as bytes.
        :return: The decompressed byte string.
        """
        return zlib.decompress(compressed_data)

    def get(self, url: str, delay=DELAY) -> str:
        """
            add caching capabilities
        """
        one_proxy = None

        cached_content = self._get_cached_content(url)

        if cached_content[0]:
            logger.info(f"Cache hit for {url}")
            return cached_content
        if self._is_proxylist_empty():
            self._download_proxy_list()
        try:
            if not self.proxy_on:
                logger.info(f"retrieve {url} without proxy")
                response = self.scraper.get(url, timeout=self.timeout)

                time.sleep(delay)
                if self.caching:
                    self._cache_content(url, response.content)
                return response.content

            while True:
                one_proxy = self._get_random_proxy(self.cursor)
                if not one_proxy:
                    raise ValueError("No proxies available")

                proxies = {'http': one_proxy, 'https': one_proxy}
                response = self.scraper.get(url, proxies=proxies, timeout=self.timeout)
                logger.info(f"Request successful using proxy: {one_proxy}")
                if response.status_code == 407:
                    raise requests.HTTPError('Proxy Authentication Required (407)')
                logger.info(f"Delay / tempo btw 2 requests {delay} ms")
                time.sleep(delay)
                self._cache_content(url, response.content)
                return response.content
        except (requests.RequestException, ValueError) as e:
            logger.error(f"Request failed")
            if one_proxy:
                self.proxy_queue.put(one_proxy)
  



         


if __name__ == "__main__":
    try:
        proxy = Proxy()
        proxy.start_cleaning()
        response = proxy.get("https://www.cnn.com")
        print(response)
    finally:
        proxy.stop_cleaning()
        proxy._remove_failed_proxies()
        proxy.close()




