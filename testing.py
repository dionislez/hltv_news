from requests_html import AsyncHTMLSession
import cloudscraper
from pyppeteer import launch
import requests
import cfscrape
import asyncio

LINK = 'https://www.hltv.org/stats/players/11893/zywoo'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 YaBrowser/23.3.3.719 Yowser/2.5 Safari/537.36',
    'sec-ch-ua': 'Chromium";v="110", "Not A(Brand";v="24", "YaBrowser";v="23',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': 'Windows',
    'referer': 'https://www.hltv.org/stats/players/11893/zywoo',
    'cookie': 'MatchFilter={%22active%22:false%2C%22live%22:false%2C%22stars%22:1%2C%22lan%22:false%2C%22teams%22:[]}; CookieConsent={stamp:%27v73i272TNna8rwXxFMvPFhUVd6eXD+CtK6lFavZy4FzBhjqoPtUIKA==%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cmethod:%27explicit%27%2Cver:1%2Cutc:1673855220679%2Cregion:%27ru%27}; google-analytics_v4__ga4=ef2bd9ee-8803-4883-b4b5-a5a22ab3b332; _pbjs_userid_consent_data=3524755945110770; __gads=ID=db7954d1df4e1f6f:T=1675613980:S=ALNI_MZPGWEXvZSBmZW33Ookn6Zd5k6zTQ; _hjSessionUser_3266621=eyJpZCI6Ijc3NWM0MDMzLWZkOTgtNTA2OC1hYWY0LThiMGY0Y2VhYWVmMSIsImNyZWF0ZWQiOjE2NzU2MjYzNDIwMjMsImV4aXN0aW5nIjpmYWxzZX0=; google-analytics_v4__counter=158; google-analytics_v4__session_counter=14; google-analytics_v4__let=1675686956087; cf_zaraz_google-analytics_v4_8565=true; google-analytics_v4_8565__ga4=ef2bd9ee-8803-4883-b4b5-a5a22ab3b332; statsTablePadding=small; nightmode=off; __qca=P0-95102567-1682485415239; trackWebVitals=no; _ga=GA1.2.1747256542.1673855222; utag_main=v_id:0187bc04d1d10017e09ea4bb9f5c0508f003008700978$_sn:1$_se:38$_ss:0$_st:1682489351642$ses_id:1682486645202%3Bexp-session$_pn:26%3Bexp-session$dcsyncran:1%3Bexp-session$appnexus_sync_session:1682486645202%3Bexp-session$dc_visit:1$dc_event:38%3Bexp-session$dc_region:eu-central-1%3Bexp-session; _ga_LQGNR7N0RS=GS1.1.1682495369.3.1.1682495370.0.0.0; _lr_geo_location=RU; __gpi=UID=00000bafd814a656:T=1675613980:RT=1683378118:S=ALNI_MatEp2B1mn6owzqlCj3cMThOJEBhg; __cf_bm=y0pdO0QHTuz8g9BuxAMddxQBHqqESs3KQV3MXDKEP7I-1683379957-0-AQGUIThUcO1whv6BpSQiVRnc4a9eopPGI/kAn5aSbQuA0VsVja8vEmYrFsqFHcIWtLduTcuo+xN7TFV5sf8+100=; google-analytics_v4_8565__ga4sid=1856248795; google-analytics_v4_8565__session_counter=70; outbrain_cid_fetch=true; google-analytics_v4_8565__engagementPaused=1683379967555; google-analytics_v4_8565__engagementStart=1683379970311; google-analytics_v4_8565__counter=1141; google-analytics_v4_8565__let=1683379970311',
    'accept-language': 'ru,en;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'scheme': 'https',
    'path': '/cdn-cgi/zaraz/t',
    'content-type': 'application/json',
    'origin': 'https://www.hltv.org'
}

# HEADERS = {
#     'referer': 'https://www.hltv.org/stats',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
# }
# COOKIES = {'hltvTimeZone': 'Europe/Copenhagen'}

# async def parsss():
#     asession = AsyncHTMLSession()
#     r = await asession.get(LINK, headers=HEADERS, cookies=COOKIES)
#     print(r.text)

# async def parsss():
#     scraper = cfscrape.create_scraper()
#     response = scraper.get(LINK)
#     print(response.content)

# async def parsss():
#     browser = await launch(headless=True)
#     page = await browser.newPage()
#     await page.waitForSelector('stats-row')
#     content = await page.content()
#     print(content)
#     await browser.close()

def check():
    r = requests.get(LINK, headers=HEADERS)
    x = r.text
    print(x)

if __name__ == '__main__':
    check()