from bs4 import BeautifulSoup, Tag
import requests as r
import json,os
from http.cookiejar import LWPCookieJar,Cookie
COOKIE_FILE = "cookie.lwp"
SESSION_FILE = 'session.json'
URL = "https://siege.hackclub.com"

lastHeader = {}
projectList = []
jar = None
sessionData = {}
session = ""
def new_cookie(name:str,value):
    targetCookie = Cookie(
    version=0,
    name=name,
    value=value,
    port=None, port_specified=False,
    domain=URL, domain_specified=True, domain_initial_dot=False,
    path="/", path_specified=True,
    secure=True,
    expires=None,
    discard=False,
    comment=None,
    comment_url=None,
    rest={"HttpOnly": None},
    rfc2109=False,
    )
    jar.set_cookie(targetCookie) # type: ignore
    jar.save(ignore_discard=True,ignore_expires=True) # type: ignore
    return targetCookie

def test_cookies():
    print("cookies might be missing or malformed")
    err = ""
    if not os.path.exists(COOKIE_FILE):
        err = "file_not_exists"
    if err == "":
        with open(COOKIE_FILE) as file:
            if not ("e" in file.read()):
                err = "empty_file"
            else:
                testJar = LWPCookieJar(COOKIE_FILE)
                testJar.load()
                testJarDict = r.utils.dict_from_cookiejar(testJar)
                print(testJarDict)
                try:
                    print(f"cf {testJarDict["cf_clearance"]}")
                except Exception:
                    pass
                try:
                    print(f"session {testJarDict["_siege_session"]}")
                except Exception:
                    pass
                if not (("cf_clearance" in testJarDict.keys()) and not (testJarDict["cf_clearance"] == "")):
                    #holy logic soup
                    #in this branch, cf_clearance is missing
                    if not (testJarDict["_siege_session"] and not (testJarDict["_siege_session"] == "")):
                        #in this branch, session is also missing
                        #i dont even know what i am doing at this point
                        #i guess the double negation is for lazy eval of the dictionary
                        #don't want an indexerror
                        err = "both_unspecified"
                    else:
                        #session isn't missing, cf_clearance is the only one
                        err = "cf_clearance_unspecified"
                elif not(("_siege_session" in testJarDict.keys()) and not (testJarDict["_siege_session"] == "")):
                    err = "_siege_session_unspecified"
    print(err)
    if err == "":
        pass
    elif err == "_siege_session_unspecified":
        newSession = input("enter your _siege_session:\n")
        new_cookie("_siege_session",newSession)
    elif err == "cf_clearance_unspecified":
        newCfClearance = input("enter your cf_clearance:\n")
        new_cookie("cf_clearance",newCfClearance)
    else:
        newSession = input("enter your _siege_session:\n")
        newCfClearance = input("enter your cf_clearance:\n")
        new_cookie("_siege_session",newSession)
        new_cookie("cf_clearance",newCfClearance)
    return err




def init():
    global jar,sessionData, session
    jar = LWPCookieJar(COOKIE_FILE)
    try:
        jar.load()
    except FileNotFoundError:
        pass
    except Exception as _:
        print(_)
    with open(SESSION_FILE) as file:
        sessionData = json.load(file)
    test_cookies()
    session = r.Session()
    session.cookies = jar #type: ignore
init()

#note: siege does some funky stuff with cookies
#apparently, it gets rotated every request, with the server response's
#Set-Cookie header being saved as HttpOnly for the next request
#i will probably need to obtain my own cookie at once
def page_soup(path,cookie=None):
    global lastHeader, jar
    if cookie:
        res = session.get(f"{URL}/{path}",headers={"Cookie":f"_siege_session={cookie}"}) # type: ignore
    else:
        res = session.get(f"{URL}/{path}") # type: ignore
    print(res.status_code)
    if res.status_code == 404:
        raise Exception(f"server returned 404 for url {URL}/{path}")
    elif res.status_code > 299 and not res.status_code == 404:
        newCookie = input(f"server returned {res.status_code}, 500 is typical for auth error.\ninput _siege_session cookie:\n")
        res = session.get(f"{URL}/{path}",headers={"Cookie":f"_siege_session={newCookie}"}) # type: ignore
        print(f"retry got {res.status_code}")
        if res.status_code > 299:
            print(f"current cf_clearance starts with {sessionData["cf_clearance"][:10]}")
            newCfClearance = input("retrying, input cf_clearance:\n")
            print(f"new cf_clearance starts with {newCfClearance[10:]}")
            res = session.get(f"{URL}/{path}", # type: ignore
                              headers={"Cookie":f"_siege_session={newCookie}"})
            if res.status_code > 299:
                raise Exception(f"err {res.status_code}")
            else:
                jar.clear("siege.hackclub.com","/","cf_clearance") #type: ignore
                new_cookie("cf_clearance",newCfClearance) #remove the previous cf_clearance, write the new one
    lastHeader = res.headers
    print(lastHeader)
    jar.save(ignore_discard=True,ignore_expires=True) # type: ignore
    return BeautifulSoup(res.content,"html.parser")

class ProjectData:
    def __init__(self,numID,projectName) -> None:
        self.ID = numID
        self.name = projectName

def addProject(card):
    cardOverlay = card.find("a",attrs={"class":"project-card-overlay"})
    projID = cardOverlay.get("href")[10:] # type: ignore
    cardHeader = card.find("div",attrs={"class":"project-header"})
    print(cardHeader)
    projTitle = cardHeader.h3.string # type: ignore
    projWeek = cardHeader.span.string # type: ignore
    projectList.append(ProjectData(projID,projectName=projTitle))
    projectList[-1].week = projWeek
    projDesc = card.find("p",attrs={"class":"project-description"}).string # type: ignore
    projTags = card.find("div",attrs={"class":"project-tags"}).find_all("div") # type: ignore
    projHackatimeName = projTags[0].find("span").string # type: ignore
    projLinks = card.find("div", attrs={"class":"project-links"}).find_all("a")
    projRepoLink = projLinks[0].get("href")
    projDemoLink = projLinks[1].get("href")
    projectList[-1].hackatimeName = projHackatimeName
    projectList[-1].repo = projRepoLink
    projectList[-1].demo = projDemoLink
    projectList[-1].soupTags = projTags
    return projectList[-1]

if True:
    with open("relevant-project-list.html") as file:
        projListHtml = file.read()
    projListSoup = BeautifulSoup(projListHtml,"html.parser")
    
else:
    projListSoup = page_soup("projects")
for card in projListSoup.find_all("article"):
        addProject(card)
