from bs4 import BeautifulSoup
import requests as r
import json
SESSION_FILE = 'session.json'
with open(SESSION_FILE) as file:
    sessionData = json.load(file)
session = r.Session()
lastHeader = {}
#note: siege does some funky stuff with cookies
#apparently, it gets rotated every request, with the server response's
#Set-Cookie header being saved as HttpOnly for the next request
#i will probably need to obtain my own cookie at once
def page_soup(url,cf_clearance,cookie=None):
    global lastHeader
    if cookie:
        res = session.get(url,headers={"cookie":f"_siege_session={cookie}"})
    else:
        res = session.get(url)
    print(res.status_code)
    lastHeader = res.headers
    print(lastHeader)
    return BeautifulSoup(res.content,"html.parser")
