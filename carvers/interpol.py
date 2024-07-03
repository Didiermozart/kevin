"""Kevin Project"""

import json
import os

import multiprocessing


from urllib.parse import urlparse, urlunparse

from scraperSeleniun import *


url = "https://ws-public.interpol.int/notices/v1/red?nationality=RU&page=1&resultPerPage=100"

def get_images(thumbnail_url, person_name):
    """
    get all images via thumbnail link
    """
    parsed_url = urlparse(thumbnail_url)
    new_path = "/".join(parsed_url.path.split('/')[:-1])

    images_url = urlunparse(parsed_url._replace(path=new_path))

    json_data = selenium_scraper(images_url, type="json")
    images = json_data.get('_embedded', {}).get('images', [])
    os.makedirs('images', exist_ok=True)

    for i, image_info in enumerate(images):
            image_url = image_info.get('_links', {}).get('self', {}).get('href')
            if image_url:
                # Télécharger l'image
                img_path = selenium_scraper(image_url, type="image")
                curdir = os.path.dirname(os.path.abspath(__file__))
                img_path = os.path.join(curdir, img_path)
                if img_path is not None:
                    # Enregistrer l'image localement
                    new_path = os.path.join('images', f'{person_name}.{i}.jpeg')
                    os.rename(img_path, new_path)
                else:
                    print(f"Failed to download image from {image_url}")

def get_all_recipes(shortList=[], url=None):

    jsondata = selenium_scraper(url=url, type="json")

    notices = jsondata['_embedded']['notices']
    query = jsondata['query']
    totalCount = jsondata['total']
    nextUrl = jsondata['_links']['next']['href']

    for recipe in notices:
        try:
            name = recipe['name']
            forname = recipe['forename']
        except:
            forname = ""
        
        thumbnail_url = recipe['_links']['thumbnail']['href']
        selenium_scraper(url=thumbnail_url, type="image")
        print( f"{forname}, {name}")
        photo_id = thumbnail_url.split('/')[-3]

        person_name = forname + "." + name
        get_images(thumbnail_url, person_name)
        element = {"name": name, "forname": forname, "thumbnail": photo_id}
        shortList.append(element)
    
    if len(shortList) == totalCount:
        return shortList
    else:
        print(len(shortList),"/", totalCount )
        print(nextUrl)
        get_all_recipes(shortList, nextUrl)



### VERSION KID
# if __name__ == "__main__":
#     nationalities = ["RU", "FR"]

#     for nationality in nationalities: 
#         url = f"https://ws-public.interpol.int/notices/v1/red?nationality={nationality}&page=1&resultPerPage=10"
#         list = get_all_recipes(url=url)

### VERSION ROOKY
def fetch_data(nationality):
    url = f"https://ws-public.interpol.int/notices/v1/red?nationality={nationality}&page=1&resultPerPage=10"
    result = get_all_recipes(url=url)
    return result



if __name__ == "__main__":
    nationalities = ["RU", "FR"]
    
    if mode == "KID":
        for nationality in nationalities:
            result = fetch_data(nationality)

    else:
        # Utilisation d'un pool de processus
        with multiprocessing.Pool(processes=len(nationalities)) as pool:
            results = pool.map(fetch_data, nationalities)
        
        # Si vous avez besoin de traiter les résultats, vous pouvez le faire ici
        for result in results:
            print(result)