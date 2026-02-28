import urllib.request
import json
req = urllib.request.Request('http://127.0.0.1:8000/openapi.json')
openapi = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
print('/generate-summary' in openapi['paths'])
