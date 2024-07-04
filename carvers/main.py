from flask import Flask, request, jsonify, render_template
import os
import sys


# current_dir = os.path.dirname(os.path.realpath(__file__))
# sys.path.insert(0, current_dir)

# try:
#     files_and_directories = os.listdir(current_dir)
#     for item in files_and_directories:
#         print(item)
# except FileNotFoundError:
#     print(f"Directory '{current_dir}' not found.")
# except PermissionError:
#     print(f"Permission denied to access directory '{current_dir}'.")


# List all files and directories in the specified path
# files_and_directories = os.listdir(current_dir)

# # Print the list
# for item in files_and_directories:
#     print(item)

from urllib.parse import urlparse, urlunparse
from scraperSeleniun import *

app = Flask(__name__)



@app.route('/')
def index():
    try:
        # Fetch data from REST Countries API
        print("get root")
        response = requests.get('https://restcountries.com/v3.1/all')
        countries = response.json()
        country_list = list()
        # Extract country names
        for country in countries:
            item = {
                'flag' : country['flag'],
                'code' : country['cca2'],
                'name' : country['name']['common'],
                }
            
            try:
                url = f"https://ws-public.interpol.int/notices/v1/red?nationality={item['code']}&resultPerPage=160&page=1"
                response = selenium_scraper(url, type="json")
                item["total_red"] = response['total']
                print(country['name']['common'], response['total']) 
                country_list.append(item)
            except:
                pass

        return render_template('index.html', countries=country_list)
    
    except Exception as e:
        return f"Error fetching data: {str(e)}"


# Route pour télécharger les images en fonction de la nationalité
@app.route('/download_images', methods=['POST'])
def download_images():
    data = request.get_json()

    if 'nationality' not in data:
        return jsonify({'error': 'Nationality is required'}), 400
    
    nationality = data['nationality']

    # Appeler votre fonction de téléchargement d'images
    result = fetch_data(nationality)

    return jsonify({'result': result}), 200

def fetch_data(nationality):
    # Appeler votre fonction existante pour obtenir les données
    url = f"https://ws-public.interpol.int/notices/v1/red?nationality={nationality}&page=1&resultPerPage=10"
    result = get_all_recipes(url=url)
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
