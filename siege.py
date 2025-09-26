from bs4 import BeautifulSoup
import requests as r
import json
SESSION_FILE = 'session.json'
with open(SESSION_FILE) as file:
    sessionData = json.load(file)
session = r.Session()
def page_soup(url):
    res = session.get(url)
    return BeautifulSoup(res.content,"html.parser")
