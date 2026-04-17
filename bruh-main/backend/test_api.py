import urllib.request, json, urllib.error
data = {'messages': [{'role': 'user', 'content': 'hi'}], 'language': 'en', 'age': 30, 'gender': 1, 'name': 'User'}
req = urllib.request.Request('http://127.0.0.1:8000/chat', data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print(f"ERROR {e.code}: {e.read().decode()}")
