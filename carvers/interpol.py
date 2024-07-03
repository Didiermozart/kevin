"""Kevin Project"""

import json
from scraperSeleniun import *


url = "https://ws-public.interpol.int/notices/v1/red?nationality=RU&page=1&resultPerPage=100"

def get_all_recipes(shortList=[], url=None):

    jsondata = selenium_scraper(url=url, type="json")

    notices = jsondata['_embedded']['notices']
    query = jsondata['query']
    totalCount = jsondata['total']
    nextUrl = jsondata['_links']['next']['href']

    for recipe in notices:
        try:
            forname = recipe['forname']
        except:
            forname = ""
        
        name = recipe['name']
        photo_url = recipe['_links']['thumbnail']['href']
        selenium_scraper(url=photo_url, type="image")
        print( f"{forname}, {name}")
        photo_id = photo_url.split('/')[-3]

        element = {"name": name, "forname": forname, "thumbnail": photo_id}
        shortList.append(element)
    
    if len(shortList) == totalCount:
        return shortList
    else:
        print(len(shortList),"/", totalCount )
        print(nextUrl)
        get_all_recipes(shortList, nextUrl)


nationality = "RU"
url = f"https://ws-public.interpol.int/notices/v1/red?nationality={nationality}&page=1&resultPerPage=10"

list = get_all_recipes(url=url)