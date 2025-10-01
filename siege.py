from bs4 import BeautifulSoup, Tag
import requests as r
import json,os,argparse
from http.cookiejar import LWPCookieJar,Cookie
import lxml
COOKIE_FILE = "cookie.lwp"
SESSION_FILE = 'session.json'
URL = "https://siege.hackclub.com"
HTML_PARSER = "html.parser"
debugBool = False

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
    global sessionData
    print("testing cookies")
    err = ""
    if not os.path.exists(COOKIE_FILE):
        err = "file_not_exists"
    if err == "":
        with open(COOKIE_FILE) as file:
            if not ("e" in file.read()):
                err = "empty_or_malformed_file"
            else:
                testJar = LWPCookieJar(COOKIE_FILE)
                testJar.load()
                testJarDict = r.utils.dict_from_cookiejar(testJar)
                #print(testJarDict)
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
    if err != "":
        print(f"cookie test: {err}")
    if err == "":
        pass
    elif err == "_siege_session_unspecified" or err == "file_not_exists" or err == "empty_or_malformed_file":
        newSession = input("enter your _siege_session:\n")
        new_cookie("_siege_session",newSession,save=True)
    elif err == "cf_clearance_unspecified":
        newCfClearance = input("enter your cf_clearance:\n")
        new_cookie("cf_clearance",newCfClearance) #no saving because i only want it in the session's jar
        sessionData = {"cf_clearance":newCfClearance}
        with open(SESSION_FILE,"w") as file:
            json.dump(sessionData,file)
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
        print("cookie file not found")
    except Exception as _:
        print(_)
    try:
        with open(SESSION_FILE) as file:
            sessionData = json.load(file)
    except FileNotFoundError:
        newCfClearance = input("enter the cf_clearance cookie:\n")
        sessionData = {"cf_clearance": newCfClearance}
        with open(SESSION_FILE,"w") as file:
            json.dump(sessionData,file)
    new_cookie("cf_clearance",sessionData["cf_clearance"])
    test_cookies()
    session = r.Session()
    session.cookies = jar #type: ignore

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
    return BeautifulSoup(res.content,HTML_PARSER)

def get_image(soup: BeautifulSoup, divclass = "project-screenshots"):
    imgDiv = soup.find("div",attrs={"class":divclass})
    #print(imgDiv)
    if imgDiv == None:
        print(f"image not present in page, class {divclass}")
        return ("",b"")
    #detailsDiv = soup.find("div",attrs={"class":"project-details"})
    #print(detailsDiv)
    link = imgDiv.find("img").get("src") #type: ignore
    res = session.get(link) #type: ignore
    if debugBool:
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
        self.week = "Week unknown"
        self.siegeTime = ""
        self.soupTags = ""
        self.imgLink = ""
        self.linkPart = "armory"
        self.screenshotData = b''

def addProject(card):
    global projectList, projectListID
    cardOverlay = card.find("a",attrs={"class":"project-card-overlay"})
    if cardOverlay.get("href")[1] == "a":
        projID = cardOverlay.get("href")[8:]
        if debugBool:
            print(f"armory project {projID}")
        oldProject = False
    else:
        projID = cardOverlay.get("href")[10:] # type: ignore
        oldProject = True
    if debugBool:
        print(f"project overlay link {cardOverlay.get("href")}")
    cardHeader = card.find("div",attrs={"class":"project-header"})
    projTitle = cardHeader.h3.string # type: ignore
    projWeek = cardHeader.span.string # type: ignore
    projectList.append(ProjectData(int(projID),projectName=projTitle))
    projectListID.append(int(projID))
    if oldProject:
        projectList[-1].linkPart = "projects"
    #add projectlist object
    projectList[-1].week = projWeek
    projDesc = card.find("p",attrs={"class":"project-description"}).string # type: ignore
    projTags = card.find("div",attrs={"class":"project-tags"}).find_all("div") # type: ignore
    projHackatimeName = projTags[0].find("span").string # type: ignore
    projLinks = card.find("div", attrs={"class":"project-links"}).find_all("a")
    projRepoLink = projLinks[0].get("href")
    projDemoLink = projLinks[1].get("href")
    projSiegeTime = card.find("div",attrs={"class":"project-time"}).string.strip()
    projPageRes = session.get(f"{URL}/projects/{projID}") #type: ignore
    if projPageRes.status_code > 299:
        raise Exception(f"addProject {projID} page returned {projPageRes.status_code}")
    else:
        projPageSource = projPageRes.content
    projImageLink, projImageContent = get_image(BeautifulSoup(projPageSource,HTML_PARSER)) #type: ignore
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

def file_format(path,fileContent,octet=False):
    imgName = os.path.basename(path)
    try:
        imgExt = os.path.splitext[1][1:]
    except Exception:
        imgExt = ""
    if octet:
        imgTuple = (imgName,fileContent,"application/octet-stream")
    elif imgExt and imgExt != "" and imgExt != "mp4":
        imgTuple = (imgName,fileContent,f"image/{imgExt}")
    else:
        imgTuple = (imgName,fileContent)
    return imgTuple

def edit_project(ID: int | str,
                 proj_name: str | None = None, desc: str | None = None,
                 repo: str | None = None, demo: str | None = None,
                 hackatime_project: str | None = None, screenshot_path: str | None = None,
                remove_scr="false",send_request=True, show_content=False):
    soup = page_soup(f"projects/{ID}/edit")
    csrf,authentic = soup_to_edit_keys(soup)
    try:
        listPos = projectListID.index(ID)
    except ValueError:
        print(f"project {ID} is not in your projects")
        return ("project_not_found_in_list",404)
    proj = projectList[listPos] #type: ProjectData
    if proj_name == None or proj_name == proj.name:
        proj_name = proj.name
    if desc == None or desc == proj.desc:
        desc = proj.desc
    if repo == None or repo == proj.repo:
        repo = proj.repo
    if repo == "#":
        print("repo fix")
        repo = "" #fix wrong detection of an unspecified link
    if demo == None or demo == proj.demo:
        demo = proj.demo
    if demo == "#":
        print("demo fix")
        demo = ""
    if hackatime_project == None or hackatime_project == proj.hackatimeName:
        hackatime_project = proj.hackatimeName
    if screenshot_path == None or screenshot_path == "":
        screenshot_data = proj.screenshotData
    else:
        with open(screenshot_path,"rb") as file:
            screenshot_data = file.read()
    #if type(screenshot_data) == bytes:
    #    screenshot_data = str(screenshot_data)[2:-1] #cut off b''
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
               "Referer":f"{URL}/{proj.linkPart}/{ID}/edit",
               "Host":"siege.hackclub.com",
               "x-csrf-token":csrf}
    req = r.Request("POST",f"{URL}/{proj.linkPart}/{ID}",headers,
                    {"project[screenshot]":file_format(screenshot_path,screenshot_data)},formData)
    if send_request:
        prepReq = session.prepare_request(req) #type: ignore
        if True:
            print(prepReq.headers)
            if show_content:
                print("========\n========\n========")
                print(prepReq.body[1000:1500])
                print("========")
        res = session.send(prepReq,timeout=10,allow_redirects=False) #type: ignore
        print(f"project edit {res.status_code}")
        if res.status_code == 404:
            print(f"project {ID} not found, returned 404")
        elif res.status_code == 422:
            print("the dev done goofed up")
        elif res.status_code > 399:
            if not show_content:
                print(res.content)
            try:
                print(res.json())
            except Exception:
                print("json error")
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
        print(f"project edit returned {res.status_code}")
        return(("sent",res.status_code))
    else:
        print(formData)
        return ("dummy",0)



def project_nice_view(proj:ProjectData):
    print("--------")
    print(f"[{proj.week}] {proj.name} (ID {proj.ID}):")
    print(f"  {proj.desc}")
    if ({proj.hackatimeName} != None) and proj.hackatimeName != "" and proj.hackatimeName != "#":
        print(f"  Hackatime {proj.hackatimeName} ({proj.siegeTime})")
    if proj.repo != "":
        print(f"  Repo {proj.repo}")
    if proj.demo != "":
        print(f"  Demo {proj.demo}")

def arg_operate():
    global HTML_PARSER
    parser = argparse.ArgumentParser(description="Utility for listing and updating your Siege projects")
    parser.add_argument("cmd",default="list",choices=["list","edit","show"])
    parser.add_argument("-l","--lxml",action="store_true",help="Use a faster parser (LXML). Use if you installed it: 'pip install lxml'")
    updateGroup = parser.add_argument_group("Update","Arguments for updating your project's info")
    updateGroup.add_argument("-i","--id",default=0,type=int,help="Siege project ID. Needed for project updating.",required=False)
    updateGroup.add_argument("-t","--title",required=False)
    updateGroup.add_argument("-b","--description",required=False)
    updateGroup.add_argument("-d","--demo",help="Project demo link",required=False)
    updateGroup.add_argument("-r","--repo",help="Project repository link",required=False)
    updateGroup.add_argument("-s","--screenshot",help="Path from cwd to the new screenshot file",required=False)
    updateGroup.add_argument("-x","--remove-screenshot",help="Flag for removing the current screenshot",action="store_true")
    updateGroup.add_argument("-w","--hackatime",help="Hackatime project name",required=False)
    args = parser.parse_args()
    if args.lxml:
        HTML_PARSER = "lxml"
    if args.cmd == "list":
        for project in projectList:
            project_nice_view(project)
    elif args.cmd == "edit":
        if args.remove_screenshot:
            remove_scr = "true"
        else:
            remove_scr = "false"
        if args.id == 0:
            raise Exception(f"To update a project, specify the project ID. Choose out of {projectListID}")
        print(edit_project(args.id,proj_name=args.title,desc=args.description,
                     repo=args.repo,demo=args.demo,hackatime_project=args.hackatime,
                     screenshot_path=args.screenshot,remove_scr=remove_scr))
    elif args.cmd == "show":
        if args.id == 0:
            raise Exception(f"To show a project, specify the project ID. Choose out of {projectListID}")
        listPos = projectListID.index(args.id)
        project_nice_view(projectList[listPos])
    


init()
if False:
    with open("relevant-project-list.html") as file:
        projListHtml = file.read()
    projListSoup = BeautifulSoup(projListHtml,HTML_PARSER)
    
else:
    projListSoup = page_soup("projects")
for card in projListSoup.find_all("article"):
        addProject(card)

if __name__ == "__main__":
    arg_operate()

