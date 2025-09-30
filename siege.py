from bs4 import BeautifulSoup, Tag
import requests as r
import json,os
from http.cookiejar import LWPCookieJar,Cookie
COOKIE_FILE = "cookie.lwp"
SESSION_FILE = 'session.json'
URL = "https://siege.hackclub.com"

lastHeader = {}
projectList = []
projectListID = []
jar = None
sessionData = {}
session = ""
def new_cookie(name:str,value,save=False):
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
    if save:
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
                cfExists = ("cf_clearance" in sessionData.keys() and not sessionData["cf_clearance"] == "")
                if not ("cf_clearance" in sessionData.keys() and not sessionData["cf_clearance"] == ""):
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
    new_cookie("cf_clearance",sessionData["cf_clearance"])
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
                sessionData["cf_clearance"] = newCfClearance
                with open(SESSION_FILE,"w") as file:
                    json.dump(sessionData,file)
    lastHeader = res.headers
    #print(lastHeader)
    jar.save(ignore_discard=True,ignore_expires=True) # type: ignore
    return BeautifulSoup(res.content,"html.parser")

def get_image(soup: BeautifulSoup, divclass = "project-screenshots"):
    imgDiv = soup.find("div",attrs={"class":divclass})
    print(imgDiv)
    if imgDiv == None:
        print(f"image not present in page, class {divclass}")
        return ("",b"")
    #detailsDiv = soup.find("div",attrs={"class":"project-details"})
    #print(detailsDiv)
    link = imgDiv.find("img").get("src") #type: ignore
    res = session.get(link) #type: ignore
    print(f"image status {res.status_code}")
    if res.status_code > 299:
        raise Exception(res.status_code)
    else:
        return (link, res.content)    

def fallback_request(prep_req,threshold=399):
    newSession = input("input new _siege_session:\n")
    print(f"current session {r.utils.dict_from_cookiejar(jar)["_siege_session"][:10]}")
    print(f"new session {newSession[:10]}")
    res = session.send(prep_req,timeout=10,allow_redirects=False) #type: ignore
    if res.status_code > threshold:
        print(f"request failed with {res.status_code}")
        newCfClearance = input("input new cf_clearance:\n")
        print(f"current cf_clearance {sessionData["cf_clearance"][:10]}")
        print(f"new cf_clearance {newCfClearance[:10]}")
        res2 = session.request(prep_req,timeout=10,allow_redirects=False) #type: ignore
        if res2.status_code > threshold:
            raise Exception(f"retry request failed with {res2.status_code}")
        else:
            sessionData["cf_clearance"] = newCfClearance
            with open(SESSION_FILE,"w") as file:
                json.dump(sessionData,file)
            new_cookie("_siege_session",newSession,save=True)
            return res2
    else:
        new_cookie("_siege_session",newSession)
        return res


class ProjectData:
    def __init__(self,numID,projectName) -> None:
        self.ID = numID
        self.name = projectName
        self.hackatimeName = ""
        self.repo = ""
        self.demo = ""
        self.desc = ""
        self.siegeTime = ""
        self.soupTags = ""
        self.imgLink = ""
        self.screenshotData = b''

def addProject(card):
    global projectList, projectListID
    cardOverlay = card.find("a",attrs={"class":"project-card-overlay"})
    projID = cardOverlay.get("href")[10:] # type: ignore
    if True:
        print(f"project overlay link {cardOverlay.get("href")}")
    cardHeader = card.find("div",attrs={"class":"project-header"})
    print(cardHeader)
    projTitle = cardHeader.h3.string # type: ignore
    projWeek = cardHeader.span.string # type: ignore
    projectList.append(ProjectData(projID,projectName=projTitle))
    projectListID.append(projID)
    #add projectlist object
    projectList[-1].week = projWeek
    projDesc = card.find("p",attrs={"class":"project-description"}).string # type: ignore
    projTags = card.find("div",attrs={"class":"project-tags"}).find_all("div") # type: ignore
    projHackatimeName = projTags[0].find("span").string # type: ignore
    projLinks = card.find("div", attrs={"class":"project-links"}).find_all("a")
    projRepoLink = projLinks[0].get("href")
    projDemoLink = projLinks[1].get("href")
    projSiegeTime = card.find("div",attrs={"class":"project-time"}).string
    projPageRes = session.get(f"{URL}/projects/{projID}") #type: ignore
    if projPageRes.status_code > 299:
        raise Exception(f"addProject {projID} page returned {projPageRes.status_code}")
    else:
        projPageSource = projPageRes.content
    projImageLink, projImageContent = get_image(BeautifulSoup(projPageSource,"html.parser")) #type: ignore
    #get the respective values from the Soup object
    projectList[-1].hackatimeName = projHackatimeName
    projectList[-1].repo = projRepoLink
    projectList[-1].demo = projDemoLink
    projectList[-1].desc = projDesc
    projectList[-1].siegeTime = projSiegeTime
    projectList[-1].soupTags = projTags
    projectList[-1].imgLink = projImageLink
    projectList[-1].screenshotContent = projImageContent
    #set the object properties from the values
    return projectList[-1]



def soup_to_edit_keys(page: BeautifulSoup):
    csrf = page.find("meta",attrs={"name":"csrf-token"}).get("content") #type: ignore
    authentic = page.find("input",attrs={"name":"authenticity_token"}).get("value") #type: ignore
    return((csrf,authentic))

def edit_project(ID: int,
                 proj_name: str | None = None, desc: str | None = None,
                 repo: str | None = None, demo: str | None = None,
                 hackatime_project: str | None = None, screenshot_path: str | None = None,
                remove_scr="false",send_request=True):
    soup = page_soup(f"projects/{ID}/edit")
    csrf,authentic = soup_to_edit_keys(soup)
    try:
        listPos = projectListID.index(ID)
    except ValueError:
        return ("project_not_found",404)
    proj = projectList[listPos] #type: ProjectData
    if proj_name == None or proj_name == proj.name:
        proj_name = proj.name
    if desc == None or desc == proj.desc:
        desc = proj.desc
    if repo == None or repo == proj.repo:
        repo = proj.repo
    if demo == None or demo == proj.demo:
        demo = proj.demo
    if hackatime_project == None or hackatime_project == proj.hackatimeName:
        hackatime_project = proj.hackatimeName
    if screenshot_path == None or screenshot_path == "":
        screenshot_data = proj.screenshotData
    else:
        with open(screenshot_path,"rb") as file:
            screenshot_data = file
    if type(screenshot_data) == bytes:
        screenshot_data = str(screenshot_data)[2:-1] #cut off b''
    formData = {"_method":"patch",
                "authenticity_token":authentic,
                "remove_screenshot":remove_scr,
                "project[name]":proj_name,
                "project[description]":desc,
                "project[repo_url]":repo,
                "project[demo_url]":demo,
                "project[hackatime_projects]": "",
                "project[hackatime_projects]": hackatime_project}
    headers = {"Origin":URL,
               "Referer":f"{URL}/projects/{ID}/edit",
               "Host":"siege.hackclub.com",
               "x-csrf-token":csrf}
    req = r.Request("POST",f"{URL}/projects/{ID}",headers,
                    {"project[screenshot]":screenshot_data},formData)
    if send_request:
        prepReq = session.prepare_request(req) #type: ignore
        if True:
            print(prepReq.headers)
        res = session.send(prepReq,timeout=10,allow_redirects=False) #type: ignore
        print(f"project edit {res.status_code}")
        if res.status_code > 399:
            res = fallback_request(prepReq)
        if res.status_code < 400:
            #save the updated content to the project entry on request success
            projectList[listPos].name = proj_name
            projectList[listPos].desc = desc
            projectList[listPos].repo = repo
            projectList[listPos].demo = demo
            projectList[listPos].hackatimeName = hackatime_project
            if not (screenshot_path == None or screenshot_path == ""):
                projectList[listPos].screenshotData = screenshot_data
                newLink,newImgContent = get_image(page_soup(f"projects/{ID}"))
                projectList[listPos].imgLink = newLink
                if not screenshot_data == newImgContent:
                    #i am curious about the content returned from the cdn-ish link
                    print(f"content differs: beginning {str(screenshot_data)[:10]} vs {str(newImgContent)[:10]}")
                    print(f"end {str(screenshot_data)[-10:]} vs {str(newImgContent)[-10:]}")
        return res.status_code
    else:
        print(formData)
        return 0
        



if False:
    with open("relevant-project-list.html") as file:
        projListHtml = file.read()
    projListSoup = BeautifulSoup(projListHtml,"html.parser")
    
else:
    projListSoup = page_soup("projects")
for card in projListSoup.find_all("article"):
        addProject(card)

