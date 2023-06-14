from pickle import TRUE
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json

## CONFIG
# yourSchool: Deine Schulnummer
# yourUser: Dein Benutzername (meistens vorname.nachname)
# yourPassword: Dein Passwort
# webhook: Die URL der Discord-Webhook
# webdriver: "firefox" oder "chromium"
# noDataNotification: Soll eine Benachrichtigung kommen, wenn kein Eintrag gefunden wurde?
yourSchool = ""
yourUser = ""
yourPassword = ""
webhook = ""
webdriver = "firefox" 
noDataNotification = TRUE
## CONFIG END

if webdriver == "firefox":
    browser = webdriver.Firefox()
elif webdriver == "chromium":
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("headless")

    browser = webdriver.Chrome(options=chromeOptions)
else:
    raise SystemExit("'webdriver' nicht definiert!")

today = date.today().strftime("%d_%m_%Y")
today_readable = date.today().strftime("%d.%m.%Y")

def getSPH():
    browser.get('https://start.schulportal.hessen.de/'+yourSchool)
    Wait(browser, timeout=20).until(EC.element_to_be_clickable(browser.find_element(By.ID, 'inputPassword')))

    username = browser.find_element(By.ID, 'username2')
    password = browser.find_element(By.ID, 'inputPassword')
    username.send_keys(yourUser)
    password.send_keys(yourPassword + Keys.RETURN)
    Wait(browser, timeout=20).until(EC.url_matches('https://start.schulportal.hessen.de/index.php'))
    return TRUE

def getSubstitutePlan():    
    browser.get('https://start.schulportal.hessen.de/vertretungsplan.php')
    Wait(browser, timeout=20).until(EC.url_matches('https://start.schulportal.hessen.de/vertretungsplan.php'))
    return TRUE

def getSubstituteDate():
    tableDivs = browser.find_elements(By.XPATH,f"//div[starts-with(@id,'tag{today}')]")
    for e in tableDivs:
        header = e.find_element(By.TAG_NAME,"h3").text
        return header

def getSubstituteData():
    tableDivs = browser.find_elements(By.XPATH,f"//div[starts-with(@id,'tag{today}')]")
    substitutionData = []
    noSubstitution = []
    for e in tableDivs:
        rows = e.find_elements(By.TAG_NAME,"tr")
        for e in rows:
            dataCell = e.find_elements(By.TAG_NAME,"td")
            for e in dataCell[:1]:
                dataTitle = e.get_attribute("title")
                substitutionData.append(dataTitle)
                dataText = e.text
                noSubstitution.append(dataText)

    if 'Keine Einträge! Aktuell liegen für die angemeldete Person keine Meldungen über Vertretungen vor!' in noSubstitution:
        return noSubstitution
    else:
        return substitutionData

def sendDiscordMessage(payload):
    if getSubstituteDate() == None & noDataNotification == TRUE:
        r = requests.post(webhook, json={"embeds": [{"title": f"Kein Eintrag am {today_readable} vorhanden!","description": "","color": 16711680,"footer": {"text": ""},"author": {"name": ""},"fields": []}]})
    elif 'Keine Einträge! Aktuell liegen für die angemeldete Person keine Meldungen über Vertretungen vor!' in payload:
        r = requests.post(webhook, json={"embeds": [{"title": f"Keine Vertretung am {today_readable}","description": "","color": 16711680,"footer": {"text": ""},"author": {"name": ""},"fields": []}]})
    else:
      fields = []
      for e in payload:
          fields.append('{"name": "%s", "value": ""}' % (e))
      fields = ', '.join(fields)      
      data_str = '{"embeds":[{"title":"Vertretung am '+str(today_readable)+'","description":"","color":32768,"footer":{"text":""},"author":{"name":""},"fields":['+str(fields)+']}]}'
      data_json = json.loads(data_str)
      r = requests.post(webhook, json=data_json)

getSPH()
getSubstitutePlan()
sendDiscordMessage(getSubstituteData())
