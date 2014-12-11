# -*- coding: utf-8 -*-
from lxml import html
import os.path
import re
import metautils
from dbsettings import settings


city = 'arnsberg'
portalname = u'arnsberg.de/open-data'
catalog_start_page_url = 'http://www.arnsberg.de/open-data/index.php'

categories = ['abfall', 'bevoelkerung', 'gis', 'bauen', 'einrichtungen', 'haushalt']


category_to_odm_map = {
    'abfall': u'Sonstiges',  # maybe infrastruktur ?
    'bevoelkerung': u'Bevölkerung',
    'gis': u'Geographie, Geologie und Geobasisdaten',
    'bauen': u'Infrastruktur, Bauen und Wohnen',
    'einrichtungen': u'Infrastruktur, Bauen und Wohnen',  # maybe soziales?
    'haushalt': u'Öffentliche Verwaltung, Haushalt und Steuern'}


def category_url(cat):
    return 'http://www.arnsberg.de/open-data/' + cat + '/index.php'


def scrape_row(row):
    d = {}
    d['title'] = row.xpath("td[1]/a[1]")[0].text
    d['url'] = "http://www.arnsberg.de" + row.xpath("td[1]/a/@href")[0]
    d['formats'] = [os.path.splitext(d['url'])[1][1:].upper()]
    d['temporalextent'] = row.xpath("td[3]")[0].text
    return d


def scrape_table(content):
    table = content.xpath('//div[@id="content"]/table[@class="contenttable"]')[0]
    rows = table.xpath('//tr')
    return map(scrape_row, rows[1:])


def scrape_subpage_urls(url):
    page = html.parse(url)
    content = page.xpath('//div[@id="content"]')[0]
    lst = content.xpath('ul[@class="headlinelist"]//li//a/@href')
    urls = map(lambda x: 'http://www.arnsberg.de' + x, lst)
    return urls


def scrape_category(url, category):
    page = html.parse(url)
    content = page.xpath('//div[@id="content"]')[0]
    ds = []
    if content.xpath('table[@class="contenttable"]'):
        ds = scrape_table(content)
    else:
        urls = scrape_subpage_urls(url)
        for u in urls:
            ds.extend(scrape_category(u, category))
    for d in ds:
        d['categories'] = category
    return ds


def gather():
    ds = []
    for c in categories:
        ds.extend(scrape_category(category_url(c), c))
    return ds


def import_data(rec):
    rec['originating_portal'] = portalname
    rec['city'] = city
    rec['source'] = 'd'
    rec['publisher'] = ''
    rec['description'] = None
    rec['costs'] = None
    rec['metadata_xml'] = None
    rec['spatial'] = False
    rec['categories'] = [category_to_odm_map[rec['categories']]]
    rec['filelist'] = []
    rec['metadata'] = ''

    # according to http://www.arnsberg.de/open-data/nutzungsbedingungen.php
    # nothing seems to be marked different
    rec['licenseshort'] = 'dl-de-zero-2.0'
    rec['open'] = metautils.isopen(rec['licenseshort'])

    # If a year of the 21st century is in the title use it as the temporalextent
    # insted of the date the file was added.
    # This is inconsistend but still better?
    t = re.search(r'20\d\d', rec['title'])
    if t: rec['temporalextent'] = t.group(0)

    return rec


def arnsberg():
    g = gather()
    dataForDB = map(import_data, g)
    metautils.setsettings(settings)
    metautils.addSimpleDataToDB(dataForDB,
                                portalname,
                                checked=True,
                                accepted=True,
                                remove_data=True)
arnsberg()
