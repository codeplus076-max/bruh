import urllib.request, os, json
from dotenv import load_dotenv
load_dotenv('backend/.env')
key = os.getenv('MAPS_API_KEY')
url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=19.24,73.12&radius=5000&type=hospital&key={key}'
try:
    res = urllib.request.urlopen(url).read()
    print(json.loads(res)['status'])
    print(json.loads(res).get('error_message', 'No error message'))
except Exception as e:
    print(e)
