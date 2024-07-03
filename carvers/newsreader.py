import logging
import pprint
import newspaper
from newspaper import Source
from newspaper.source import Category, Feed
from datetime import datetime

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.query import dict_factory

from urllib.parse import urljoin, urlsplit, urlunsplit


# logger = logging.getLogger(__name__)

try:
    from services.newspapers.scraperProxy import *
except:
    from scraperProxy import * 



newsList = [
    { "url":"http://lemonde.fr", "lang":"fr"},
    { "url":"https://edition.cnn.com", "lang":"us"},
    {"url":"https://fortinet.com/blog/threat-research", "lang":"us"},
    {"url":"https://bleepingcomputer.com/news/security", "lang":"us"},
    {"url":f"https://thehackernews.com/YEAR/MONTH".replace("YEAR", str(datetime.now().year)).replace("MONTH",datetime.now().strftime('%m')), "lang":"us"}
    ]



proxy = Proxy()



def download_categories_proxy(news):
    # download categories
    categories_urls = [c.url for c in news.categories]
    for index, category_url in enumerate(categories_urls):
        news.categories[index].html = proxy.get(category_url)
    return [c for c in news.categories if c.html]


def set_feeds_proxy(news):
    common_feed_urls = ['/feed', '/feeds', '/rss']
    common_feed_urls = [urljoin(news.url, url) for url in common_feed_urls]
    common_feed_urls_as_categories = [Category(url=url) for url in common_feed_urls]

    category_urls = [c.url for c in common_feed_urls_as_categories]
    for index, category_url in enumerate(category_urls):
        try:
            responseTxt = proxy.get(category_url)
            if responseTxt is None:
                raise Exception
            common_feed_urls_as_categories[index].html = responseTxt
        except:
            pass

    common_feed_urls_as_categories = [c for c in common_feed_urls_as_categories if c.html]
    
    for _ in common_feed_urls_as_categories:
            doc = news.config.get_parser().fromstring(_.html)
            _.doc = doc

    common_feed_urls_as_categories = [c for c in common_feed_urls_as_categories if
                                          c.doc is not None]
  
    categories_and_common_feed_urls = news.categories + common_feed_urls_as_categories
    urls = news.extractor.get_feed_urls(news.url, categories_and_common_feed_urls)
    return [Feed(url=url) for url in urls]

def download_feeds_proxy(news):
    """
    download all feeds
    """
    feeds = None
    feeds_url = [f.url for f in news.feeds]
    for index, url in enumerate(feeds_url):
        
        try:
            news.feeds[index].rss = proxy.get(url)
        except:
            logger.warning(('Deleting feed %s from source %s due to '
                             'download error') %
                             (news.categories[index].url, news.url))
        feeds = [f for f in news.feeds if f.rss]
    return feeds
    

#### trace ==>
# news = Source(url)
# news.html = proxy.get(url)
# news.parse()
# news.set_categories()
# news.categories = download_categories_proxy(news)
# news.parse_categories()
# # news.set_feeds()
# news.feeds = set_feeds_proxy(news)


# news.download_feeds()
# news.generate_articles()

##### end trace ==>

def build(url):
    s = newspaper.build(url)
    for article in s.articles:
        article.html = proxy.get(article.url)

    # if url is  None:
    #     return
    # news = Source(url)
    # news.html = proxy.get(url)
    # news.parse()
    # news.set_categories()
    # news.categories = download_categories_proxy(news)
    # news.parse_categories()
    # news.feeds = set_feeds_proxy(news)
    # news.feeds = download_feeds_proxy(news)
    # news.generate_articles()
    # return news


def getArticles(url):
    logger.info(f"A / url : {url}")
    news = build(url)
    print(news.articles)
    logger.info(f" count articles : {news.articles}")
    articles = list()
    # Loop through the articles
    for index, article in enumerate(news.articles):
        logger.info(f"article index: {index}")
        
        try:
            logger.info(f"article: {article.url}")
            #get raw html page 
            response = proxy.get(article.url)
            # parse article
            article.download(input_html=response)
            article.parse()
            article.nlp()

            # Extract article data
            article_data = {
                'url': article.url,
                'publish_date': str(article.publish_date),  # Convert to string if not None
                'authors': article.authors,      
                # 'text': article.text,
                'top_image': article.top_image,
                'movies': article.movies,
                'title': article.title,
                'summary': article.summary,
                'keywords': article.keywords
            }

            # logger.info("article", article_data['url'])
            articles.append(article_data)

        except Exception as e:
            logger.error(f"Failed to process article {article.url}: {e}")

    return articles
