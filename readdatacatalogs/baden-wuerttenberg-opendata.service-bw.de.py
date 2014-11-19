# -*- coding: utf-8 -*-
import urllib2
import re
import itertools
from lxml import etree
import metautils
from dbsettings import settings

portalname = u'opendata.service-bw.de'
catalog_start_page_url = "http://opendata.service-bw.de/Seiten/offenedaten.aspx"


def getRecordHtmlTree(htmlUrl):
    response = urllib2.urlopen(htmlUrl)
    htmlStr = response.read()
    htmlTree = etree.HTML(htmlStr)
    return htmlTree


def licenseToODM(licenseEntry):
    if licenseEntry == u'Namensnennung':
        odmLicense = 'CC BY 3.0 DE'
    elif licenseEntry == u"Maps4BW kann im Rahmen der Umsetzung der Open-Data-Strategie des Ministeriums f\xfcr L\xe4ndlichen Raum und Verbraucherschutz Baden-W\xfcrttemberg unter den Bedingungen der Lizenz CC BY 3.0 (":
        odmLicense = u'CC BY 3.0 DE'
    elif licenseEntry == u'Namensnennung, nicht kommerziell, Weitergabe unter gleichen Bedingungen':
        odmLicense = u'CC BY-NC-SA 3.0 DE'
    elif licenseEntry == u'Keine freie Lizenz, siehe Internetseite des Datensatzes':
        odmLicense = u'other-closed'
    else:
        odmLicense = u'nicht bekannt'
    return odmLicense


def formatToODM(formatStr):
    """Returns the "allowedFormats" strings found in the argument,
    that are sourrounded by either a whitespace, a comma, a slash or brackets"""
    allowedFormats = list(metautils.fileformats) + ['PDF', 'HTML']
    fs = []
    for f in allowedFormats:
            p = re.compile("[\s,/\(]" + f + "[\s,/\)]", re.IGNORECASE)
            if p.search(' ' + formatStr + ' '):
                fs.append(f)
    return fs


def extractUrl(urlStump):
    if urlStump[:5] == "http:":
        url = urlStump
    elif urlStump[:11] == "/Documents/":
        url = u"http://" + portalname + urlStump
    else:
        url = u"http://" + portalname + u"/Seiten/" + urlStump
    return url


def nextCatalogPage(page):
    try:
        pageNavTable = page.xpath('//table[@class="ms-bottompaging"]')[0]
        forwardButton = pageNavTable.xpath('//td[@class="ms-paging"]/following-sibling::*')[0]
        onclick = forwardButton.xpath('a/@onclick')[0]
        link = re.findall('"([^"]*)"', onclick)[0]
        url = "http://" + portalname + link
        page = getRecordHtmlTree(url.replace(u"\\u0026", "&"))
    except:
        page = None
    return page


def getCatalogPages():
    page = getRecordHtmlTree(catalog_start_page_url)
    pages = []
    while page is not None:
        pages.append(page)
        page = nextCatalogPage(page)
    return pages


def getCatalogEntryUrls(catalogPage):
    entryListItems = catalogPage.xpath('//div[@class="OdpVList"]//div[@class="OdpVListElem"]')
    domain = "http://" + portalname + "/Seiten/"
    getRecordUrl = lambda listItem: domain + listItem.xpath('.//a/@href')[0]
    entryPages = map(getRecordUrl, entryListItems)
    return entryPages


def scapeTableCell(table, cellName):
    try:
        row = table.xpath('.//tr[td//text()[contains(., "' + cellName + '")]]')[0]
        cell = row.xpath('td')
        val = cell[1].text
    except:
        val = ""
    return val


def scrapeLicense(page):
        cell = page.xpath('.//table[2]/tr[2]/td[2]/node()')[0]
        try:
            cell = cell.xpath('./text()')[0]
        except:
            None
        return cell


def scrapeCatalogEntryPage(url):
    page = getRecordHtmlTree(url)
    p = page.xpath('//div[@class="OdpVListElem details"]')[0]

    d = dict()
    d['page-url'] = url
    d['title']               = p.xpath('./div/h1/text()')[0]
    d['description']         = p.xpath('.//div[2]/p/text()')[0]
    d['format']              = scapeTableCell(p.xpath('.//div[4]/table')[0], 'Format')
    d['url']                 = page.xpath('.//div[4]/table//a/@href')[0]
    d['nutzungsbedingungen'] = scrapeLicense(p)
    d['herausgeber']         = scapeTableCell(p.xpath('.//div[6]//table')[0], 'Herausgeber des Datensatzes:')
    d['beschreibende stelle']= scapeTableCell(p.xpath('.//div[6]//table')[0], 'Datensatz beschreibende Stelle:')  # unused

    d['stichtag'] = scapeTableCell(p.xpath('./table')[0], 'Stichtag:')
    d['zeitraum'] = scapeTableCell(p.xpath('./table')[0], 'Zeitraum:')
    d['publiziert am'] = scapeTableCell(p.xpath('.//div[6]//table')[0], 'Zuletzt publiziert oder aktualisiert')
    return d


def toDB(rec):
    db = {}
    db['city'] = ''  # Baden-Württenberg is not a city ?!
    db['source'] = 'd'
    db['costs'] = None
    db['categories'] = [u'Noch nicht kategorisiert']

    db['url'] = rec['page-url']
    db['title'] = rec['title']
    db['description'] = rec['description']
    db['publisher'] = rec['herausgeber']
    db['filelist'] = [extractUrl(rec['url'])]
    db['formats'] = formatToODM(rec['format'])
    db['licenseshort'] = licenseToODM(rec['nutzungsbedingungen'])
    temps = filter(lambda x: x != "",
                   [rec['zeitraum'], rec['stichtag'], rec['publiziert am']])
    db['temporalextent'] = temps[0] if temps else None

    db['open'] = metautils.isopen(db['licenseshort'])
    db['spatial'] = False

    db['metadata'] = db.copy()
    db['metadata_xml'] = None

    return db


def badenWuerttenberg():
    print "Get Catalog Entries"
    catalogPages = getCatalogPages()
    catalogEntryUrls = map(getCatalogEntryUrls, catalogPages)
    catalogEntryUrls = list(itertools.chain(*catalogEntryUrls))

    print "Scrape Catalog Entries"
    catalogDicts = map(scrapeCatalogEntryPage, catalogEntryUrls)
    dataForDB = map(toDB, catalogDicts)

    print "Write to db"
    metautils.setsettings(settings)
    metautils.addSimpleDataToDB(dataForDB,
                                portalname,
                                checked=True,
                                accepted=True,
                                remove_data=True)

badenWuerttenberg()
