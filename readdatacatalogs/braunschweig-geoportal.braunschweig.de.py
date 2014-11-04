import urllib2
from lxml import etree
from lxml.builder import ElementMaker
import braunschweig_utils
import pprint
import re
import metautils
from dbsettings import settings

pp = pprint.PrettyPrinter(indent=4)

portalname = 'geoportal.braunschweig.de'
url = 'http://geoportal.braunschweig.de/soapServices/CSWStartup'
braunschweigMetaDataFile = '../metadata/braunschweig/catalog.xml'
numRecordsPerRequest = 50  # max 100

ns_csw = 'http://www.opengis.net/cat/csw/2.0.2'
ns_ogc = 'http://www.opengis.net/ogc'
ns_xsi = 'http://www.w3.org/2001/XMLSchema-instance'

E = ElementMaker(namespace=ns_csw,
                 nsmap={'csw': ns_csw,
                        'ogc': ns_ogc,
                        'xsi': ns_xsi})


def getRecordsRequestXml(startPosition=1, maxRecords=10):
    getR = E.GetRecords(
        E.Query(E.ElementSetName('full'),
                {'typeNames': 'csw:Record'}),
        {'service': 'CSW',
         'version': '2.0.2',
         'resultType': 'results',
         'startPosition': str(startPosition),
         'maxRecords': str(maxRecords),
         'outputFormat': 'application/xml',
         'outputSchema': ns_csw})
    return etree.tostring(getR, pretty_print=True)


def getRecordsRequest(url, startPos):
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


def extractRecords(getRecordsResponseXml):
    recs = getRecordsResponseXml.xpath(
        '/csw:GetRecordsResponse/csw:SearchResults//csw:Record',
        namespaces={'csw': ns_csw})
    return recs


def getRecords():
    print 'Get Catalog Records'
    req = getRecordsRequest(url, 1)
    num = numberOfRecordsMatched(req)

    searchResults = req.xpath(
        '/csw:GetRecordsResponse/csw:SearchResults',
        namespaces={'csw': ns_csw})

    searchResults[0].set('numberOfRecordsReturned', str(num))
    for n in range(numRecordsPerRequest + 1, num + 1, numRecordsPerRequest):
        nextReq = getRecordsRequest(url, n)
        rs = extractRecords(nextReq)
        for r in rs:
            searchResults[0].append(r)

    return req




def getRecordHtmlTree(idStr):
    htmlUrl = 'http://geoportal.braunschweig.de/terraCatalog/' \
              'Query/ShowCSWInfo.do;?fileIdentifier=' + idStr
    response = urllib2.urlopen(htmlUrl)
    htmlStr = response.read()
    htmlTree = etree.HTML(htmlStr)
    return htmlTree


# first guess for mapping of categories, needs to be revised
categorieToODMmap = {
    'OGC Web Catalog Service'         : [],
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
    'transportation'                  : u'Transport und Verkehr',
    'structure'                       : u'Infrastruktur, Bauen und Wohnen',
    'society'                         : u'Bevölkerung',
    'climatologyMeteorologyAtmosphere': u'Umwelt und Klima',
    'farming'                         : u'Wirtschaft und Arbeit',
    'economy'                         : u'Wirtschaft und Arbeit'}

# only the ones used right now 
allowedFormats = ['TIFF', 'DXF', 'Shape', 'ASCII', 'XLS',
                  'CityGML', '3D-Shape', 'OBJ', 'MDB Multipatch',
                  'DGM', 'DOM', 'PDF', 'JPG', 'AI',
                  'Papierkarte', 'Karte', 'Faltblatt', u'Broschüre']


def categoriesToODM(categorieList):
    allCats = []
    for categorieStr in categorieList:
        cats = categorieStr.split(',')
        cats = [categorieToODMmap[i.strip()] for i in cats]
        allCats.extend(cats)
    if allCats != [[]]:
        allCats = list(set(allCats))
    return cats  

# Includes the weird cases of
# 'digitales Geländemodell (DGM) oder digitales Oberflächenmodell (DOM)' and
# 'Papierkarte (auf Anfrage)', while trying to avoid false positives
def formatsToODM(formatList):
    '''Returns the "allowedFormats" strings found in the argument,
    that are sourrounded by either a whitespace, a comma, a slash or brackets'''
    fs = []
    for formatsStr in formatList:
        for f  in allowedFormats:
            p = re.compile("[\s,/\(]" + f + "[\s,/\)]", re.IGNORECASE)
            if p.search(' ' + formatsStr + ' '):
                fs.append(f)
    return fs

def licenseToODM(licenceList):
    if 'Datenlizenz Deutschland - Namensnennung - Version 1.0' in licenceList :
        return 'dl-de-by-1.0'
    elif u'unbeschränkt' in licenceList:
        return "other-open"
    elif u'keine' in licenceList: # Use limitations keine bedeutet offene lizenz?
        return "other-open"
    elif licenceList == []:
        return "nicht bekannt"
    else :
        return 'other-closed'
    


def getCategories(htmlTree): # unused
    cats = htmlTree.xpath('//div[@id="CategoryWrapper"]/table/tbody//td')[1]
    return [cats.text] + [t.tail for t in cats[0:-1]]

def getTopicCategories(htmlTree):
    cats = htmlTree.xpath('//div[@id="CategoryWrapper"]/table/tbody//td')[2]
    return [cats.text]  + [t.tail for t in cats[0:-1]]

def getOrganisation(htmlTree):
    org = htmlTree.xpath('//div[@id="ResourceWrapper"]/table/tbody//td')[10]
    return org.text


def extractRecordTag(rec, xpathStr, oneEntryExpectey=True):
    entry = rec.xpath(
        './/' + xpathStr,
        namespaces={'csw': ns_csw,
                    'dc': 'http://purl.org/dc/elements/1.1/',
                    'dct': 'http://purl.org/dc/terms/'})

    value = [e.text for e in entry]
    value = list(set(value))
    if oneEntryExpectey:
        if value == []:
            value = ''
        else:
            value = value[0]
        
    return value

def extractData(rec):
    d = dict()

    d['identifier']  = extractRecordTag(rec, 'dc:identifier')
    d['title']       = extractRecordTag(rec, 'dc:title')
    d['abstract']    = extractRecordTag(rec, 'dct:abstract')
    d['created']     = extractRecordTag(rec, 'dct:created')
    d['rights']      = extractRecordTag(rec, 'dc:rights', False)
    d['accessRights']= extractRecordTag(rec, 'dct:accessRights', False)
    d['modified']    = extractRecordTag(rec, 'dct:modified')
    d['spatial']     = extractRecordTag(rec, 'dct:spatial', False)
    d['type']        = extractRecordTag(rec, 'dc:type')
    d['format']      = extractRecordTag(rec, 'dc:format', False)
    d['subject']     = extractRecordTag(rec, 'dc:subject', False)

    
    d['xml'] = etree.tostring(rec, pretty_print=True, encoding='utf8')
    d['url'] = 'http://geoportal.braunschweig.de/terraCatalog/Query/' \
               'ShowCSWInfo.do;?fileIdentifier=' + d['identifier']

    pageHtml = getRecordHtmlTree(d['identifier'])
    d['categories'] = getCategories(pageHtml)
    d['Topic category'] = getTopicCategories(pageHtml)
    d['organisation'] = getOrganisation(pageHtml)

    return d


def recordToDB(rec):
    db = {} 
    db['city'] = 'braunschweig'
    db['originating_portal'] = portalname
    db['source'] = 'd'

    db['url'] = rec['url']
    db['title'] = rec['title']
    db['description'] = rec['abstract']
    db['temporalextent'] = rec['created']
    db['publisher'] = rec['organisation']
    db['metadata_xml'] = rec['xml']

    db['formats'] = formatsToODM(rec['format'])
    db['licenseshort'] = licenseToODM(rec['rights'])
    db['categories'] = categoriesToODM(rec['Topic category'])

    db['costs'] = ''
    db['spatial'] = False
    db['filenames'] = []
    db['metadata_json'] = '{}'
    
    return db


def writeRecToDB(rec, checked = False, accepted = False):
    cur = metautils.getDBCursor(settings)
    cur.execute("INSERT INTO data \
    (city, originating_portal, source, url, title, formats, description, \
    temporalextent, licenseshort, costs, publisher, spatial, categories, \
    checked, accepted, filelist, metadata, metadata_xml) \
    SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s \
    WHERE NOT EXISTS ( \
    SELECT url FROM data WHERE url = %s  )",
    (rec['city'],
     rec['originating_portal'],
     rec['source'],
     rec['url'],
     rec['title'],
     rec['formats'],
     rec['description'],
     rec['temporalextent'],
     rec['licenseshort'],
     rec['costs'],
     rec['publisher'],
     rec['spatial'],
     rec['categories'],
     checked,
     accepted,
     rec['filenames'],
     rec[u'metadata_json'],
     rec[u'metadata_xml'],
     rec['url']))


def braunschweigGeoportal():
    recs = getRecords()

    xmlString = etree.tostring(recs, pretty_print=True)
    with open(braunschweigMetaDataFile, 'w') as f:
        f.write(xmlString.encode('utf8'))

    
    recDict = map(extractData, (extractRecords(recs)))
    datafordb = map(writeRecToDB, recDict)
    
    metautils.removeDataFromPortal(portalname)
    map (recToDB, datafordb)
    metautils.dbCommit()


braunschweigGeoportal()    

