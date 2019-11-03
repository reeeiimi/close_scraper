import urllib3
from bs4 import BeautifulSoup as bs
import gspread
import csv
import re
import certifi
from oauth2client.service_account import ServiceAccountCredentials
import requests
import time

'''
    SS：https://docs.google.com/spreadsheets/d/1yCm3-MLU7a3qMFRkJgv-vZ_p7M4C-D7XYLgogq8Sklg/edit#gid=0
    name: title
        形式：【閉店】神戸クックワールドビュッフェ網干店

    最終更新日：body > div.wrapper > div.detail.post-206464.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-niigata.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_meta > span.post_time > time
        ハイフン区切り(2019-10-28)

    属性：body > div.wrapper > div.detail.post-206464.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-niigata.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_meta > span.post_cat
        子要素：a要素、rel = category tag

    住所：#address > tbody

    閉店日：div.col-md-8.mainarea > div.detail_text > div.post_body > h3
           body > div.wrapper > div.detail.post-206459.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-kanagawa.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_body > h3 
        形式：新潟県長岡市 2019年9月30日（月）閉店

'''
def WriteSS(row, sendList):
    #ss
    scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('/Users/reimi/Documents/10291320/dip/dip-scraper-255308-034b6a2ca233.json', scope)
    gc = gspread.authorize(credentials)
    doc = gc.open('close list')
    wks = doc.worksheet('シート1')

    cells = wks.range(row, 1, row + 101, 18)
    i = 0
    for r in sendList:
        for c in r:
            cells[i].value = c
            i += 1
    wks.update_cells(cells)



update_sel = 'div.col-md-8.mainarea > div.detail_text > div.post_meta > span.post_time > time'
date_sel = 'div.col-md-8.mainarea > div.detail_text > div.post_body > h3'
attribute_sel = 'div.col-md-8.mainarea > div.detail_text > div.post_meta > span.post_cat'

# get url list
urlList = []
errorList = []
with(open("/Users/reimi/Documents/10291320/dip/data/close_list.csv", encoding="shift_jis")) as f:
    reader = csv.reader(f)
    for r in reader:
        urlList.append(r)

#urlList = ['https://kaiten-heiten.com/hottomotto-nagaokaooshima/']
# qrole
sendList = []
count = 0
num = 0
current_row = 2
temp = 42592
# sqrape
for url in urlList:
    print(count, num, url[0])
    if(num<42590):
        num += 1
        continue
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    req = http.request('GET', url[0])
    if(req.status == 200):
        soup = bs(req.data, 'html.parser')
        # get update date
        try:
            update = soup.select_one(update_sel).get_text()
            update_el = re.sub(r'/−|‐|－|₋|_|̄̄̄|⁻|‾|ー|-|‑|–|—|―|ｰ/', '-', update).split('-')
            update = '/'.join(update_el)
            #print(update)
        except Exception as e:
            print('update error:', type(e))
            errorList.append(url[0])

        # get date
        try:
            date = soup.select_one(date_sel).get_text()
            date_groups = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date)
            if(not date_groups):
                date_groups = re.search(r'(\d{4})年(\d{1,2})月(.+)閉店', date)
            date = '/'.join(date_groups.groups())
            #print(date)
        except Exception as e:
            print('date error:', type(e))
            errorList.append(url[0])

        # get address and postal code
        try:
            ad_tr = soup.findAll('tr')
            for ad in ad_tr:
                if(re.search(r'住所', ad.get_text())!= None):
                    address = ad.td.find_next_sibling().get_text()
                    #print(address)
                    break;
                else:
                    address = None
            if(address == None):
                ValueError
            
            address = re.sub(r'/−|‐|－|₋|_|̄̄̄|⁻|‾|ー|-|‑|–|—|―|ｰ/', '-', address)
            address = address.replace('〒', '')
            address = address.replace(' ', '')
            pc_match = re.search(r'\d\d\d-\d\d\d\d',address)
            if(pc_match):
                postalcode = pc_match.group()
                _address = address.replace(postalcode, '')
                if(re.search(r'\d\d\d-\d\d\d\d', _address)):
                    address = address
                else:
                    address = _address
            else:
                pc_match = re.search(r'(\d{3})(\d{4})', address)
                if(pc_match):
                    postalcode = '-'.join(pc_match.groups())
                    address = address.replace(postalcode, '', address)
                else:
                    postalcode = '記載なし'
            
            #print(postalcode, address)
        except Exception as e:
            postalcode = None
            print("address error:", type(e))
            errorList.append(url[0])

        # get attribute
        try:
            attribute = [att.get_text() for att in soup.findAll('a', attrs = { 'rel': 'category tag' })]
            if(len(attribute) < 10):
                attribute.extend(['' for i in range(10 - len(attribute))])
            #print(attribute)
        except Exception:
            print('attribute error:', type(e))
            errorList.append(url[0])

        # get name
        try:
            title_tag = soup.title
            title = title_tag.string
            title = re.sub(r'【.+】', '', title)
            print(title)
        except Exception as e:
            print('title error:', type(e))
            errorList.append(url[0])
            

        # create list
        try:
            sendList.append([])
            sendList[count].extend([update, 'CLOSE', title, date, postalcode, address, '掲載なし', url[0]])
            sendList[count].extend(attribute)
            count += 1
            #print(sendList, '\n')
        except Exception as e:
            print(count, ":error:", type(e), e.args)
            errorList.append(url[0])
    else:
        print(count)
        errorList.append(url[0])

    if(count == 30):
        WriteSS(temp, sendList)
        sendList = []
        temp = temp + count
        count = 0

    time.sleep(1)
    num += 1

with(open('/Users/reimi/Documents/10291320/dip/data/errorList.csv', encoding='shift_jis')) as f:
    writer = csv.writer(f)
    writer.writerow(errorList)



