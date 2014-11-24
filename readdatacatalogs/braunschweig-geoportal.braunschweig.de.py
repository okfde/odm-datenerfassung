# -*- coding: utf-8 -*-
import urllib2
import re
from lxml import etree
from lxml.builder import ElementMaker
import metautils
from dbsettings import settings


portalname = 'geoportal.braunschweig.de'
apiUrl = 'http://geoportal.braunschweig.de/soapServices/CSWStartup'
braunschweigMetaDataFile = '../metadata/braunschweig/catalog.xml'

ns_csw = 'http://www.opengis.net/cat/csw/2.0.2'
ns_ogc = 'http://www.opengis.net/ogc'
ns_xsi = 'http://www.w3.org/2001/XMLSchema-instance'


def getRecordsRequestXml(startPosition, numRecordsPerRequest):
    """Returns the XML for the 'getRecords' post request
    of the Catalogue Service Web (CSW)"""

    E = ElementMaker(namespace=ns_csw,
                     nsmap={'csw': ns_csw,
                            'ogc': ns_ogc,
                            'xsi': ns_xsi})

    getR = E.GetRecords(
        E.Query(E.ElementSetName('full'),
                {'typeNames': 'csw:Record'}),
        {'service': 'CSW',
         'version': '2.0.2',
         'resultType': 'results',
         'startPosition': str(startPosition),
         'maxRecords': str(numRecordsPerRequest),
         'outputFormat': 'application/xml',
         'outputSchema': ns_csw})
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
        '/csw:GetRecordsResponse/csw:SearchResults//csw:Record',
        namespaces={'csw': ns_csw})
    return recs


def getRecords():
    """Request all records in the Catalogue Service Web (CSW).
    Puts together the requests for certain ranges of records
    (since only maximal number of a 100 records per request is
    premitted by the api) for later output as a single XML file."""

    numRecordsPerRequest = 50  # maximum 100
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


def getRecordHtmlTree(idStr):
    """Fetches the html page of the record with the identifier "idStr"
    in the braunschweig metadata catalog"""
    htmlUrl = 'http://geoportal.braunschweig.de/terraCatalog/' \
              'Query/ShowCSWInfo.do;?fileIdentifier=' + idStr
    response = urllib2.urlopen(htmlUrl)
    htmlStr = response.read()
    htmlTree = etree.HTML(htmlStr)
    return htmlTree


# first guess for mapping of categories, needs to be revised
categorieToODMmap = {
    'OGC Web Catalog Service'         : [],  # mark as 'nicht kategorisiert'?
    'INSPIRE Other Service'           : [],
    'INSPIRE Discovery Service'       : [],
    'geoscientificInformation'        : u'Geographie, Geologie und Geobasisdaten',
    'boundaries'                      : u'Geographie, Geologie und Geobasisdaten',
    'OGC Web Map Service'             : u'Geographie, Geologie und Geobasisdaten',
    'elevation'                       : u'Geographie, Geologie und Geobasisdaten',
    'planningCadastre'                : u'Geographie, Geologie und Geobasisdaten',
    'imageryBaseMapsEarthCover'       : u'Geographie, Geologie und Geobasisdaten',
    'location'                        : u'Geographie, Geologie und Geobasisdaten',
    'health'                          : u'Gesundheit',
    'environment'                     : u'Umwelt und Klima',
    'biota'                           : u'Umwelt und Klima',
    'climatologyMeteorologyAtmosphere': u'Umwelt und Klima',
    'transportation'                  : u'Transport und Verkehr',
    'structure'                       : u'Infrastruktur, Bauen und Wohnen',
    'society'                         : u'Bevölkerung',
    'farming'                         : u'Wirtschaft und Arbeit',
    'economy'                         : u'Wirtschaft und Arbeit'}


braunschweigSpecificFormats = [
    'DXF', 'ASCII', 'CityGML', '3D-Shape', 'OBJ',
    'MDB Multipatch', 'DGM', 'DOM', 'PDF', 'JPG', 'AI',
    'Papierkarte', 'Karte', 'Faltblatt', u'Broschüre']
allowedFormats = list(metautils.allfiletypes) + braunschweigSpecificFormats


def categoriesToODM(categorieList):
    """Maps the braunschweig categories (the "topic categories" from the
    catalog webpages) to the ODM categories"""
    allCats = []
    for categorieStr in categorieList:
        cats = categorieStr.split(',')
        cats = [categorieToODMmap[i.strip()] for i in cats]
        allCats.extend(cats)
    if allCats != [[]]:
        allCats = list(set(allCats))
    else:
	allCats = ['Noch nicht kategorisiert']
    return allCats


# Includes the weird cases of
# 'digitales Geländemodell (DGM) oder digitales Oberflächenmodell (DOM)' and
# 'Papierkarte (auf Anfrage)', while trying to avoid false positives
def formatsToODM(formatList):
    """Returns the "allowedFormats" strings found in the argument,
    that are sourrounded by either a whitespace, a comma, a slash or brackets"""
    fs = []
    for formatsStr in formatList:
        for f in allowedFormats:
            p = re.compile("[\s,/\(]" + f + "[\s,/\)]", re.IGNORECASE)
            if p.search(' ' + formatsStr + ' '):
                fs.append(f)
    return fs


def licenseToODM(licenseList):
    odmLicense = None
    if 'Datenlizenz Deutschland - Namensnennung - Version 1.0' in licenseList:
        odmLicense = 'dl-de-by-1.0'
    elif (u'keine' in licenseList) or (u'unbeschränkt' in licenseList):
        odmLicense = 'other-closed'
    elif licenseList == []:
        odmLicense = 'nicht bekannt'
    else:
        odmLicense = 'other-closed'
    return odmLicense


# add other licenses and move to metautils ?
def isOpenLicense(licenseStr):
    licenseMap = {
        'dl-de-by-1.0'  : True,
        'other-open'    : True,
        'other-closed'  : False,
        'nicht bekannt' : None}
    return licenseMap[licenseStr]


# Braunschweig also uses other geodata formats e.g.
# 'DXF', 'CityGML', '3D-Shape', 'OBJ', 'MDB Multipatch'
# but is a 'Papierkarte' a geoformat? probably not
# it represents geodata, but is no geoformat?
# but than why is tiff a geoformat? questions upon questions :)
def isSpatialFormat(formats):
    return any([f in metautils.geoformats for f in formats])


def scrapeCategories(htmlTree):
    cats = htmlTree.xpath('//div[@id="CategoryWrapper"]/table/tbody//td')[1]
    return [cats.text] + [t.tail for t in cats[0:-1]]


def scrapeTopicCategories(htmlTree):
    topicCategoriesCell = htmlTree.xpath('//div[@id="CategoryWrapper"]/table/tbody//td')[2]
    return [topicCategoriesCell.text] + [t.tail for t in topicCategoriesCell[0:-1]]


def scrapeOrganisation(htmlTree):
    organisationCell = htmlTree.xpath('//div[@id="ResourceWrapper"]/table/tbody//td')[10]
    return organisationCell.text


# includes direct links to files, and links to stuff like maps which aren't really files
# not good?
def scrapeFilelist(htmlTree):
    distTable = htmlTree.xpath('//div[@id="DistributionWrapper"]/table')[0]
    onResRow = distTable.xpath("//tr[th//text()[contains(., 'Online Resource:')]]")[0]
    onResCell = onResRow.xpath('./td')[0]
    links = onResCell.xpath('./a')
    fileList = [l.attrib['href'] for l in links]
    return fileList


def scrapeContentTypes(filelistUrls):  # unused
    expectedTypes = ['JPEG', 'PDF', 'HTML', 'PLAIN', 'ZIP']
    returnedTypes = []
    for fileUrl in filelistUrls:
        try:
            request = urllib2.Request(fileUrl)
            request.get_method = lambda: 'HEAD'
            response = urllib2.urlopen(request)
            contentType = response.info().getheader('Content-Type')
            for t in expectedTypes:
                p = re.compile(t, re.IGNORECASE)
                if p.search(contentType):
                    if t == 'PLAIN':
                        returnedTypes.append('TXT')
                    else:
                        returnedTypes.append(t)
        except:
            None  # print "Dead url in filelist: ", fileUrl

    if returnedTypes != []:
        returnedTypes = list(set(returnedTypes))
    return returnedTypes


def extractRecordTag(rec, tag, oneEntryExpected=True):
    """Gets the value(s) for the specific tag.
    Returns a list of all values if, if oneEntryExpected is set to False"""
    entry = rec.xpath(
        './/' + tag,
        namespaces={'csw': ns_csw,
                    'dc': 'http://purl.org/dc/elements/1.1/',
                    'dct': 'http://purl.org/dc/terms/'})

    values = [e.text for e in entry]
    values = list(set(values))
    if oneEntryExpected and len(values) > 0:
        values = values[0]  # hopefully the first is the relevant one
    return values


def extractData(rec):
    d = dict()
    d['identifier']  = extractRecordTag(rec, 'dc:identifier')
    d['title']       = extractRecordTag(rec, 'dc:title')
    d['abstract']    = extractRecordTag(rec, 'dct:abstract')
    d['created']     = extractRecordTag(rec, 'dct:created')
    d['rights']      = extractRecordTag(rec, 'dc:rights', False)
    d['accessRights']= extractRecordTag(rec, 'dct:accessRights', False)
    d['modified']    = extractRecordTag(rec, 'dct:modified')
    d['spatials']    = extractRecordTag(rec, 'dct:spatial', False)  # should probaly used for spatialextent?
    d['type']        = extractRecordTag(rec, 'dc:type')
    d['formats']     = extractRecordTag(rec, 'dc:format', False)
    d['subjects']    = extractRecordTag(rec, 'dc:subject', False)

    d['xml'] = etree.tostring(rec, pretty_print=True, encoding='utf8')
    d['url'] = 'http://geoportal.braunschweig.de/terraCatalog/Query/' \
               'ShowCSWInfo.do;?fileIdentifier=' + d['identifier']

    return d


def scrapeData(d):
    pageHtml = getRecordHtmlTree(d['identifier'])
    d['categoriesB'] = scrapeCategories(pageHtml)
    d['topic category'] = scrapeTopicCategories(pageHtml)
    d['organisation'] = scrapeOrganisation(pageHtml)
    d['filelist'] = scrapeFilelist(pageHtml)
    # d['filelist-content-types'] = scrapeContentTypes(d['filelist'])
    return d


def recordToDB(rec):
    db = {}
    db['city'] = 'braunschweig'
    db['source'] = 'd'
    db['costs'] = None

    db['url'] = rec['url']
    db['title'] = rec['title']
    db['description'] = rec['abstract']
    db['temporalextent'] = rec['created']
    db['publisher'] = rec['organisation']
    db['filelist'] = rec['filelist']

    db['formats'] = formatsToODM(rec['formats'])
    db['categories'] = categoriesToODM(rec['topic category'])
    db['licenseshort'] = licenseToODM(rec['rights'])
    db['open'] = isOpenLicense(db['licenseshort'])
    db['spatial'] = isSpatialFormat(db['formats'])

    additionalMetadata = ['accessRights', 'modified', 'spatials',
                          'type', 'subjects', 'categoriesB']
    db['metadata'] = dict(db.items() +
                          {key: rec[key] for key in
                           additionalMetadata}.items())

    # xml metadata only includes data from catalog api?!
    db['metadata_xml'] = rec['xml']
    return db


def braunschweigGeoportal():
    print 'Get catalog records'
    catalog = getRecords()

    xmlString = etree.tostring(catalog, pretty_print=True)
    with open(braunschweigMetaDataFile, 'w') as f:
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

braunschweigGeoportal()
