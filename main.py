import urllib3
from bs4 import BeautifulSoup as bs
import gspread
import csv
import re
import certifi
from oauth2client.service_account import ServiceAccountCredentials

'''
    SS：https://docs.google.com/spreadsheets/d/1yCm3-MLU7a3qMFRkJgv-vZ_p7M4C-D7XYLgogq8Sklg/edit#gid=0
    name: title
        形式：【閉店】神戸クックワールドビュッフェ網干店

    最終更新日：body > div.wrapper > div.detail.post-206464.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-niigata.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_meta > span.post_time > time
        ハイフン区切り(2019-10-28)

    属性：body > div.wrapper > div.detail.post-206464.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-niigata.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_meta > span.post_cat
        子要素：a要素、rel = category tag

    住所：#address > tbody > tr:nth-child(1) > td:nth-child(2)

    閉店日：body > div.wrapper > div.detail.post-206464.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-niigata.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_body > h3
        形式：新潟県長岡市 2019年9月30日（月）閉店

'''

update_sel = 'body > div.wrapper > div.detail.post-206464.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-niigata.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_meta > span.post_time > time'
date_sel = 'body > div.wrapper > div.detail.post-206464.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-niigata.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_body > h3'
address_sel = '#address > tbody > tr:nth-child(1) > td:nth-child(2)'
attribute_sel = 'body > div.wrapper > div.detail.post-206464.post.type-post.status-publish.format-standard.has-post-thumbnail.hentry.category-lunch.category-niigata.category-close.category-kantou_koushinetsu.category-restaurant > div > div > div.col-md-8.mainarea > div.detail_text > div.post_meta > span.post_cat'

'''
# get url list
urlList = []
with(open("C:/Users/Reimi/Documents/dip/data/close_list.csv", encoding="shift_jis")) as f:
    reader = csv.reader(f)
    for r in reader:
        urlList.append(r)
'''

urlList = 'https://kaiten-heiten.com/hottomotto-nagaokaooshima/'
# qrole
sendList = [[]]
iter = 0
current_row = 2
# sqrape
for url in urlList:
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    req = http.request('GET', url)
    if(req.status == 200):
        soup = bs(req.data, 'html.parser')

        # get update date
        update = soup.select_one(update_sel).get_text()
        update_el = re.sub(r'/−|‐|－|₋|_|̄̄̄|⁻|‾|ー|-|‑|–|—|―|ｰ/', '-', update).split('-')
        update = '/'.join(update_el)

        # get date
        date = soup.select_one(date_sel).get_text()
        date_groups = re.match(r'(\d\d\d\d)年(\d?)月(\d?)日')
        date = '/'.join(date_groups.groups())

        # get address and postal code
        address = soup.select_one(address_sel).get_text()
        address = re.sub(r'/−|‐|－|₋|_|̄̄̄|⁻|‾|ー|-|‑|–|—|―|ｰ/', '-', address)
        pc_match = re.match(r'\d\d\d-\d\d\d\d')
        if(pc_match):
            postalcode = pc_match.group()
            address = address.replace(postalcode, '')
        else:
            postalcode = '記載なし'

        # get attribute
        attribute = soup.findAll('a', attrs = { 'rel': 'category tag' }).get_text()

        # get name
        title_tag = soup.title
        title = title_tag.string
        title = re.sub(r'【.+】', '', title)

        # create list
        sendList.append([update, 'CLOSE', title, date, postalcode, address, '掲載なし', url].extend(attribute))
        print(sendList)
    else:
        print(iter)
    iter += 1

'''
#ss
scope = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('C:\\Users\\Reimi\\Documents\\dip\\dip-scraper-255308-034b6a2ca233.json', scope)
gc = gspread.authorize(credentials)
doc = gc.open('tweetscraper2')
wks = doc.worksheet('シート1')
'''