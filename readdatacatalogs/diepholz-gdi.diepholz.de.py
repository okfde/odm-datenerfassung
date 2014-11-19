# -*- coding: utf-8 -*-
import urllib2
from lxml import etree
from lxml.builder import ElementMaker
import metautils
from dbsettings import settings

portalname = 'gdi.diepholz.de'
apiUrl = 'http://gdi.diepholz.de/soapServices/CSWStartup'
dieholzMetaDataFile = '../metadata/diepholz/catalog.xml'

ns_csw = 'http://www.opengis.net/cat/csw/2.0.2'
ns_gmd = "http://www.isotc211.org/2005/gmd"
ns_gco = 'http://www.isotc211.org/2005/gco'
ns_xsi = 'http://www.w3.org/2001/XMLSchema-instance'


def getRecordsRequestXml(startPosition, numRecordsPerRequest):
    """Returns the XML for the 'getRecords' post request
    of the Catalogue Service Web (CSW)"""

    E = ElementMaker(namespace=ns_csw,
                     nsmap={'csw': ns_csw,
                            'gmd': ns_gmd})

    getR = E.GetRecords(
        E.Query(E.ElementSetName('full'),
                {'typeNames': 'csw:Record'}),
        {'service': 'CSW',
         'version': '2.0.2',
         'resultType': 'results',
         'startPosition': str(startPosition),
         'maxRecords': str(numRecordsPerRequest),
         'outputFormat': 'application/xml',
         'outputSchema': ns_gmd})
    return etree.tostring(getR, pretty_print=True)


def getRecordsRequest(url, startPos, numRecordsPerRequest):
    """Returns the xml returned by the getRecords' request,
    from number `startPos` to `startPos` + `numRecordsPerRequest`"""
    req = urllib2.Request(url=url,
                          data=getRecordsRequestXml(startPos,
                                                    numRecordsPerRequest),
                          headers={'Content-Type': 'application/xml'})
    req = urllib2.urlopen(req)
    xml = req.read()
    tree = etree.fromstring(xml)
    return tree


def numberOfRecordsMatched(getRecordsResponseXml):
    recs = getRecordsResponseXml.xpath(
        '/csw:GetRecordsResponse/csw:SearchResults//@numberOfRecordsMatched',
        namespaces={'csw': ns_csw})
    return int(recs[0])


def extractRecords(getRecordsResponse):
    """Returns a list of etrees of the individual
    records of a getRecords response"""
    recs = getRecordsResponse.xpath(
        '/csw:GetRecordsResponse/csw:SearchResults//gmd:MD_Metadata',
        namespaces={'csw': ns_csw,
                    'gmd': ns_gmd})
    return recs


def getRecords():
    """Request all records in the Catalogue Service Web (CSW).
    Puts together the requests for certain ranges of records
    (since only maximal number of a 100 records per request is
    premitted by the api) for later output as a single XML file."""

    numRecordsPerRequest = 10  # maximum 100
    req = getRecordsRequest(apiUrl, 1, numRecordsPerRequest)
    num = numberOfRecordsMatched(req)

    searchResults = req.xpath(
        '/csw:GetRecordsResponse/csw:SearchResults',
        namespaces={'csw': ns_csw})

    searchResults[0].set('numberOfRecordsReturned', str(num))
    for n in range(numRecordsPerRequest + 1, num + 1, numRecordsPerRequest):
        nextReq = getRecordsRequest(apiUrl, n, numRecordsPerRequest)
        rs = extractRecords(nextReq)
        for r in rs:
            searchResults[0].append(r)

    return req


def getRecordHtmlTree(htmlUrl):
    """Fetches the html page of the record with the identifier "idStr"
    in the braunschweig metadata catalog"""
    response = urllib2.urlopen(htmlUrl)
    htmlStr = response.read()
    htmlTree = etree.HTML(htmlStr)
    return htmlTree


# often really bad fit to odm kategories especially with the "Topic categories" entry
# so the "Categegories" used are used py preference
categorieToODMmap = {
    'Jugend und Soziales (Jugend und Soziales)': u'Soziales',
    'Auto und Verkehr (Auto und Verkehr)': u'Transport und Verkehr',
    '(Sicherheit und Ordnung)': u'Infrastruktur, Bauen und Wohnen',  # sounds like Gesetze und Justiz, but it actually overlaps  with planningCadastre
    'Natur und Landschaft (Natur und Landschaft)': u'Umwelt und Klima',
    '-': u'Noch nicht kategorisiert',
    'Planen und Bauen (Planen und Bauen)': u'Infrastruktur, Bauen und Wohnen',
    '(Altlasten und Altablagerungen)': u'Umwelt und Klima',
    '(basemaps)': u'Geographie, Geologie und Geobasisdaten',
    'Service und Verwaltung (Service und Verwaltung)': u'Öffentliche Verwaltung, Haushalt und Steuern',
    '(location)': u'Geographie, Geologie und Geobasisdaten',
    'Wind und Wasser (Wind und Wasser)': u'Umwelt und Klima',
    'Bildung und Kultur (Bildung und Kultur)': u'Bildung und Wissenschaft',
    'ALK (ALK)': u'Geographie, Geologie und Geobasisdaten',
    '(Regionalplanung)': u'Infrastruktur, Bauen und Wohnen',
    'Basisdaten, Kartenwerke, Luftbilder (Basisdaten Kartenwerke Luftbilder)': u'Geographie, Geologie und Geobasisdaten',
    '(Basisdaten, Kartenwerke, Luftbilder)': u'Geographie, Geologie und Geobasisdaten',
    '(service)': u'Sonstiges',  # Daten Kataloge
    'Freizeit und Tourismus (Freizeit und Tourismus)': u'Kultur, Freizeit, Sport, Tourismus',
    '(planning)': u'Infrastruktur, Bauen und Wohnen',
    u'Veterin\xe4rwesen und Verbraucherschutz (Veterin\xe4rwesen und Verbraucherschutz)': u'Verbraucherschutz',


    '': u'Noch nicht kategorisiert',
    '-': u'Noch nicht kategorisiert',
    'environment': u'Umwelt und Klima',
    'inlandWaters': u'Geographie, Geologie und Geobasisdaten',
    'transportation': u'Transport und Verkehr',
    'utilitiesCommunication': u'Infrastruktur, Bauen und Wohnen',
    'planningCadastre': u'Infrastruktur, Bauen und Wohnen',  # Infrastruktur seems the best fit here, but often its more like geobasisdaten
    'boundaries': u'Geographie, Geologie und Geobasisdaten',
    'society': u'Sonstiges',  # It sound a lot like "Bevölkerung, but the stuff in here is very diverse:
    'health': u'Gesundheit',  # it would probaly be best to use the "Categories" instead of the "Topic category" entry
    'location': u'Geographie, Geologie und Geobasisdaten',
    'elevation': u'Geographie, Geologie und Geobasisdaten',
    'structure': u'Infrastruktur, Bauen und Wohnen',
    'imageryBaseMapsEarthCover': u'Geographie, Geologie und Geobasisdaten'
}


def categoriesToODM(categorie, topicCategorie):
    """Maps the diepholz categories (the "topic categories" OR "categories" from the
    catalog webpages) to the ODM categories"""
    if categorie != "-":
        cat = categorieToODMmap[categorie.strip()]
    else:
        cat = categorieToODMmap[topicCategorie.strip()]
    return [cat]


# There seem to be no entries with open licenses,
# so I mark them all as closed.
# Where nothing is known i mark them as 'nicht bekannt'
# even though they are probably closed as well ...
def licenseToODM(licenseEntries):
    def isKnown(x):
        if x: x.strip() != '-' or x.strip() != ''

    knowns = filter(isKnown, licenseEntries)
    if knowns != []:
        odmLicense = 'other-closed'
    else:
        odmLicense = 'nicht bekannt'
    return odmLicense

def extractRecordTag(rec, tag, oneEntryExpected=True):
    """Gets the value(s) for the specific tag.
    Returns a list of all values if, if oneEntryExpected is set to False"""
    entry = rec.xpath(
        './/' + tag,
        namespaces={'csw': ns_csw,
                    'gmd': ns_gmd,
                    'gco': ns_gco})

    values = [e.text for e in entry]
    values = list(set(values))
    if oneEntryExpected and len(values) > 0:
        values = values[0]  
    return values


def extractData(rec):
    d = dict()
    d['fileIdentifier'] = extractRecordTag(rec, "gmd:fileIdentifier/gco:CharacterString")
    d['xml'] = etree.tostring(rec, pretty_print=True, encoding='utf8')
    d['url'] = 'http://gdi.diepholz.de/geodatensuche/Query/' \
               'ShowCSWInfo.do;?fileIdentifier=' + d['fileIdentifier']

    return d


def scapeTableCell(htmlTree, page, cellName):
    try:
        table = htmlTree.xpath('//div[@id="' + page + '"]/table')[0]
        row = table.xpath('//tr[th//text()[contains(., "' + cellName + '")]]')[0]
        cell = row.xpath('td')
        val = cell[0].text
    except:
        # print "notFound: " + cellName
        val = ""
    return val


def scrapeData(d):
    pageHtml = getRecordHtmlTree(d['url'])

    d['title']         = scapeTableCell(pageHtml, "ResourceWrapper", "Title:")
    d['summary']       = scapeTableCell(pageHtml, "ResourceWrapper", "Summary:")
    d['creation']      = scapeTableCell(pageHtml, "ResourceWrapper", "creation:")
    d['revision']      = scapeTableCell(pageHtml, "ResourceWrapper", "revision:")
    d['organisation']  = scapeTableCell(pageHtml, "ResourceWrapper", "Organisation:")
    d['position']      = scapeTableCell(pageHtml, "ResourceWrapper", "Position:")
    d['topicCategory'] = scapeTableCell(pageHtml, "ResourceWrapper", "Topic category:")
    d['categories']    = scapeTableCell(pageHtml, "CategoryWrapper", "Categories:")

    d['westBoundLongitude'] = scapeTableCell(pageHtml, "ResourceWrapper", "West bound longitude:")
    d['eastBoundLongitude'] = scapeTableCell(pageHtml, "ResourceWrapper", "East bound longitude:")
    d['northBoundLatitude'] = scapeTableCell(pageHtml, "ResourceWrapper", "North bound latitude:")
    d['southBoundLatitude'] = scapeTableCell(pageHtml, "ResourceWrapper", "South bound latitude:")

    d['useLimitations']    = scapeTableCell(pageHtml, "AccessWrapper", 'Use limitations:')
    d['accessConstraints'] = scapeTableCell(pageHtml, "AccessWrapper", 'Access constraints:')
    d['otherConstraints']  = scapeTableCell(pageHtml, "AccessWrapper", 'Other constraints:')

    d['onlineResources'] = scapeTableCell(pageHtml, "DistributionWrapper", 'Online Resource:')

    return d


def recordToDB(rec):
    db = {}
    db['city'] = 'diepholz'
    db['source'] = 'd'
    db['costs'] = None

    db['url'] = rec['url']
    db['title'] = rec['title']
    db['description'] = rec['summary']


    db['filelist'] = []  # this seems to be the filelist :) # http://www.lkdh.de/gis/Vorschaubilder_terraCatalog/Fachkarte_Vorrangstandorte_Windenergie_Landkreis_Diepholz_WMS.png

    db['formats'] = []  # no files, no formats ...
    db['categories'] = categoriesToODM(rec['categories'], rec['topicCategory'])
    db['licenseshort'] = licenseToODM([rec['useLimitations'], rec['accessConstraints'], rec['otherConstraints']])
    db['open'] = False  # there seems to be no open data
    db['spatial'] = False 

    if rec['revision'] != '-':
        db['temporalextent'] = rec['revision']
    else:
        db['temporalextent'] = rec['creation']

    db['publisher'] = None
    if rec['organisation'] != '-':
        db['publisher'] = rec['organisation']
    if rec['position'] != '-':
        db['publisher'] += ' - ' + rec['position']

    db['metadata'] = db.copy()
    db['metadata_xml'] = rec['xml']

    return db


def diepholzGeoportal():
    global all
    print 'Get catalog records'
    catalog = getRecords()

    xmlString = etree.tostring(catalog, pretty_print=True)
    with open(dieholzMetaDataFile, 'w') as f:
        f.write(xmlString.encode('utf8'))

    print 'Scrape catalog record entries'
    recsList = extractRecords(catalog)
    recDicts = map(extractData, recsList)
    recDicts = map(scrapeData, recDicts)
    dataForDB = map(recordToDB, recDicts)

    print 'Write to db'
    metautils.setsettings(settings)
    metautils.addSimpleDataToDB(dataForDB,
                                portalname,
                                checked=True,
                                accepted=True,
                                remove_data=True)

diepholzGeoportal()
