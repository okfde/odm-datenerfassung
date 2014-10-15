# -*- coding: utf-8 -*-
import sys
import codecs
import json
import unicodecsv as csv
import psycopg2
import psycopg2.extras
import urllib
import urllib2
import time
import xml.etree.ElementTree as etree

from collections import OrderedDict

### Interesting formats ###
geoformats = ('GEOJSON', 'GML', 'GPX', 'GJSON', 'TIFF', 'SHP', 'KML', 'KMZ', 'WMS', 'WFS', 'GML2', 'GML3', 'SHAPE')

#TODO: Define mime types also

### Database operations ###
con = None
settings = None

def setsettings(sentsettings):
    global settings
    settings = sentsettings

def getDBCursor(sentsettings, dictCursor = False):
    global con
    global settings
    
    if settings == None:
        settings = sentsettings
    
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
    
    if dictCursor:
        dictCursor = psycopg2.extras.DictCursor
    else:
        dictCursor = None
    if con:
        con.close()
    try:
        con = psycopg2.connect(database=settings['DBNAME'], user=settings['DBUSER'], password=settings['DBPASSWD'], host=settings['DBHOST'], cursor_factory=dictCursor)
        cur = con.cursor()
        return cur
    except psycopg2.DatabaseError, e:
        print 'Database error: %s' % e
        
def dbCommit():
    global con
    if con:
        con.commit()
        con.close()

#Add cities from the settlements list        
def addCities(cities, bundesland):
    cur = getDBCursor(settings)
    for city in cities:
        long_name = convertSettlementNameToNormalName(city)
        short_name = getShortCityName(city)
        print 'Trying to add ' + long_name + ' as ' + short_name + ' (supplied: ' + city + ')'
        cur.execute("INSERT INTO cities \
                    (city_shortname, city_fullname, bundesland) \
                    SELECT %s, %s, %s \
                    WHERE NOT EXISTS ( \
                        SELECT city_shortname FROM cities WHERE city_shortname = %s \
                    )",
                    (short_name, long_name, bundesland, short_name)
                   )
        cur.execute("UPDATE cities SET last_updated = current_date WHERE city_shortname = %s", (short_name,))
    dbCommit()
    print 'Updating cities with missing lat/lon info...'
    updateCitiesWithLatLong()
        
def markCityAsUpdated(city_shortname):
    cur = getDBCursor(settings)
    cur.execute("UPDATE cities SET last_update = current_date WHERE city_shortname = %s)", (city_shortname,))
    dbCommit()
    
def updateCitiesWithLatLong():
    #Assume terminal is UTF-8 compatible
    #sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    #sys.stderr = codecs.getwriter('utf8')(sys.stderr)
    cur = getDBCursor(settings)
    cur.execute('SELECT city_fullname FROM cities WHERE latitude IS NULL')
    cities = cur.fetchall()
    print str(len(cities)) + ' have missing lat/lon info'
    for row in cities:
        cur = getDBCursor(settings)
        print u"Trying to get location of " + row[0]
        url = u"https://nominatim.openstreetmap.org/search?q=" + urllib.quote_plus(row[0].encode('utf8')) + u",Germany&format=xml"
        print u"Using URL: " + url
        req = urllib2.Request(url.encode('utf8'))
        resp = urllib2.urlopen(req)
        xml = resp.read()
        root = etree.fromstring(xml)
        
        if len(root) > 0:
            print row[0] + " has coordinates " + root[0].attrib['lat'] + ", " + root[0].attrib['lon'] + ' based on \"' + root[0].attrib['display_name'] + '\"'
            cur.execute('UPDATE cities SET latitude=%s, longitude=%s WHERE city_fullname=%s', (root[0].attrib['lat'], root[0].attrib['lon'], row[0]))
        else:
            print 'WARNING: Could not get a location for ' + row[0]
        #For debugging, turn this on so as to not overload the server
        #raw_input("Press Enter to continue...")
        
        #Don't upset the server (extra cautious/friendly)
        time.sleep(1)
        dbCommit()

def getCitiesWithOpenDataPortals():
    portalcities = []
    cur = getDBCursor(settings)
    cur.execute('SELECT city_shortname FROM cities WHERE LENGTH(open_data_portal) > 0')
    for result in cur.fetchall():
        portalcities.append(result[0])
    return portalcities
    
def getCityOpenDataPortal(cityname):
    cur = getDBCursor(settings)
    cur.execute('SELECT open_data_portal FROM cities WHERE city_shortname=%s', (cityname,))
    result = cur.fetchone()[0]
    if 'http://' in result:
        return result[7:len(result)]
    else:
        return result
    
def getCitiesWithData():
    cities = []
    cur = getDBCursor(settings)
    cur.execute('SELECT DISTINCT city FROM data')
    for result in cur.fetchall():
        cities.append(result[0])
    return cities

#General purpose addition of data in Google Spreadsheets format to the DB
#If checked == True then this data is 'open data'
#If accepted == True then inter source deduplification has been performed
def addDataToDB(datafordb = [], bundesland=None, originating_portal=None, checked=False, accepted=False):
    cur = getDBCursor(settings)
    badcities = []
    
    mapping = dict()
    mapping['city'] = u'Stadt'
    mapping['source'] = u'Quelle'
    mapping['title'] = u'Dateibezeichnung'
    mapping['description'] = u'Beschreibung'
    mapping['temporalextent'] = u'Zeitlicher Bezug'
    mapping['licenseshort'] = u'Lizenz'
    mapping['costs'] = u'Kosten'
    mapping['publisher'] = u'Veröffentlichende Stelle'
    
    dictsdata = dict()
    takenrows = dict()
    
    validsources = ('m', 'd', 'c', 'g', 'b')
    
    #Check whether the cities are in the land specified
    if bundesland:
        uniquecities = getUniqueItems(datafordb, u'Stadt')
        for city in uniquecities:
            cur.execute('SELECT bundesland FROM cities WHERE city_shortname = %s', (city,))
            result = cur.fetchone()
            if result == None:
                badcities.append(city)
                print 'Warning: The city with key ' + city + ' does not exist in the DB. This shouldn\'t be possible. Please check. Not adding data from this city'
            elif result[0] != bundesland:
                badcities.append(city)
                print 'Warning: The city with key ' + city + ' is not in the Bundesland ' + bundesland + '. Please try and rename the offending city if its key is not being automatically generated, otherwise change the key generation scheme to remove the conflict. Not adding data from this city'
            
    for row in datafordb:
        if row[u'Stadt'] not in badcities:
            source = row['Quelle'].strip()
            if source not in validsources:
                print 'Error: row has an unrecognised source: ' + source + '. Not adding'
            else:
                if source not in dictsdata:
                    dictsdata[source] = []
                dictsdata[source].append(row)

    for source in validsources:
        if source in dictsdata:
            print 'Processing source: ' + source
            for row in dictsdata[source]:
                theurl = ''
        
                url = row['URL Datei'].strip()
                parent = row['URL PARENT'].strip()           
                #print 'Processing entry with parent [' + parent +'] and url [' + url + ']'

                if url != '' and parent == '':
                    theurl = url
                else:
                    theurl = parent

                #Parents are always favoured and should be unique
                #We assume that all catalog and manual entries are unique
                #Otherwise we rather aggressively expect the filenames to be unique;
                #often there is more than one way to the same file
                if (theurl not in takenrows) or source == 'd' or source == 'm':
                    row['URL'] = theurl
                    if theurl == parent and url != '':
                        row['filenames'] = [url]
                    else:
                        row['filenames'] = []
                    takenrows[theurl] = row
                else:
                    print 'Not adding: url already there, transferring filename, categories and geo'
                    if url != '':
                        takenrows[theurl]['filenames'].append(url)
                    for key in row:
                        if row[key].strip().lower() == 'x':
                             takenrows[theurl][key] = 'x'

    for row in takenrows.values():
        formats = csvtoarray(row['Format'].upper())

        categories = []
        geo = False

        for key in row:
            if type(row[key]) != list:
                if row[key].strip().lower() == 'x':
                    if key.strip().lower() == 'geo':
                        geo = True
                    else:
                        categories.append(key)

        cur.execute("INSERT INTO data \
            (city, originating_portal, source, url, title, formats, description, temporalextent, licenseshort, costs, publisher, spatial, categories, checked, accepted, filelist) \
            SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s \
            WHERE NOT EXISTS ( \
                SELECT url FROM data WHERE url = %s \
            )",
            (row['Stadt'], originating_portal, row[mapping['source']].strip(), row['URL'], row[mapping['title']].strip(),
            formats, row[mapping['description']].strip(), row[mapping['temporalextent']].strip(),
            row[mapping['licenseshort']].strip(), row[mapping['costs']].strip(),
            row[mapping['publisher']].strip(), geo, categories, checked, accepted, row['filenames'], row['URL'])
            )
            
    dbCommit()
            
def removeDataFromPortal(portalId):
    cur = getDBCursor(settings)
    cur.execute("DELETE FROM data \
            WHERE originating_portal = %s", (portalId,))
    dbCommit()

### Deal with data structures ###
def getgroupofelements(target, item):
    if target in item:
        returnstring = arraytocsv(item[target])
    return returnstring
    
def arraytocsv(arrayvalue):
    returnstring = ''
    for part in arrayvalue:
        returnstring += part + ','
        #Get rid of last commas
    returnstring = returnstring[0:len(returnstring)-1]
    return returnstring
    
def csvtoarray(csvstring):
    returnarray = csvstring.split(',')
    returnarray = [item.strip() for item in returnarray]
    return returnarray
    
def setofvaluesascsv(arrayvalue, keyvalue):
    simplearray = setofvaluesasarray(arrayvalue, keyvalue)
    return arraytocsv(simplearray)
    
def setofvaluesasarray(arrayvalue, keyvalue):
    simplearray = []
    for item in arrayvalue:
        simplearray.append(item[keyvalue])
    return simplearray
    
#Sometimes things deep in the JSON are interpreted as a string
def dequotejson(stringvalue):
    cleanvalue = stringvalue.replace('\\', '')
    cleanvalue = cleanvalue[1:len(cleanvalue)-1]
    return cleanvalue
    
def getUniqueItems(arrayofdict, key):
    mylist = [item[key] for item in arrayofdict]
    uniqueset = set(mylist)
    return list(uniqueset)
    
### End Dealing with data structures ###

### Data processing utilities ###
def extractFormat(filestring):
    return "PASS"
    
def extract_em_domain(email):
    return email.split('@')[-1]

def findLcGermanCharsAndReplace(germanstring):
    germanchars = (u'ü',u'ä',u'ö',u'é',u'ß')
    englishreplacements = ('ue', 'ae', 'oe', 'ee', 'ss')
    for x in range(0,len(germanchars)):
        if germanchars[x] in germanstring:
            germanstring = germanstring.replace(germanchars[x], englishreplacements[x])
    return germanstring
    
def convertSettlementNameToNormalName(settlementName):
    return settlementName.split(',')[0]
    
def getShortCityName(settlementName):
    long_name = convertSettlementNameToNormalName(settlementName)
    short_name = findLcGermanCharsAndReplace(long_name.replace(' ', '').replace('(', '').replace(')', '').lower())
    return short_name
### End data processing utilities ###

### Process CKAN data into files/DB output ###
#Create full empty row
def getBlankRow():
    row = OrderedDict()
    for key in getTargetColumns():
        row[key] = ''
    row[u'Quelle'] = 'd'
    row[u'Noch nicht kategorisiert'] = 'x'
    return row
  
#Our schema
def getTargetColumns():
    return [u'Quelle', u'Stadt', u'URL PARENT', u'Dateibezeichnung', u'URL Datei', u'Format', u'Beschreibung', u'Zeitlicher Bezug', u'Lizenz', u'Kosten', u'Veröffentlichende Stelle', u'geo', u'Arbeitsmarkt', u'Bevölkerung', u'Bildung und Wissenschaft', u'Haushalt und Steuern', u'Stadtentwicklung und Bebauung', u'Wohnen und Immobilien', u'Sozialleistungen', u'Öffentl. Sicherheit', u'Gesundheit', u'Kunst und Kultur', u'Land- und Forstwirtschaft', u'Sport und Freizeit', u'Umwelt', u'Transport und Verkehr', u'Energie, Ver- und Entsorgung', u'Politik und Wahlen', u'Gesetze und Justiz', u'Wirtschaft und Wirtschaftsförderung', u'Tourismus', u'Verbraucher', u'Sonstiges', u'Noch nicht kategorisiert']

def processListOfFormats(formatArray):
    geo = ''
    text = ''
    formats = []
    for format in formatArray:
        if (format.upper() not in formats):
            formats.append(format.upper())
            if (format.upper() in geoformats):
                geo = 'x'
    text = arraytocsv(formats)
    
    return [text, geo]
     
#Do a fairly simple dump of desired data and try to get the filename, geo or not, unpack categories and tags
def writerawresults(data, columns, placeholderurl, filename):
    csvoutfile = open(sys.argv[2] + '.csv', 'wb')
    datawriter = csv.writer(csvoutfile, delimiter=',')

    #Not needed in the long term. This was for comparing the file-finding capabilities of
    #of different methods
    csvfilesoutfile = open(sys.argv[2]+'.files.csv', 'wb')
    filesdatawriter = csv.writer(csvfilesoutfile, delimiter=',')
    
    row = []
    extraitems = ['format', 'geo', 'groups', 'tags']
    row.extend(extraitems);
    columnsoffset = len(extraitems)
    
    for column in columns:
        row.append(column)

    datawriter.writerow(row)
    
    for package in data:
        row = []
    
        #All files, for analysis
        dict_string = package['data_dict']
        json_dict = json.loads(dict_string)
        for resource in json_dict['resources']:
            if 'url' in resource:
                frow = []
                frow.append(resource['url'])
                filesdatawriter.writerow(frow)
    
        #Get resource formats
        if ('res_format' in package):
            [text, geo] = processListOfFormats(package['res_format'])
            row.extend([text, geo])
        else:
            row.extend('','')
    
        groups = u''
        tags = u''

        if 'groups' in package:
            row.append(arraytocsv(package['groups']))

        if 'tags' in package:
            row.append(arraytocsv(package['tags']))

        for column in columns:
            if column in package: 
                row.append(package[column])
            else:
                row.append('')

        if row[columns.index('url') + columnsoffset] == '':
            row[columns.index('url') + columnsoffset] = placeholderurl + row[columns.index('id') + columnsoffset]    
        datawriter.writerow(row)
    
    csvoutfile.close();
    csvfilesoutfile.close();

### City names database and cleaning ###
def getCities():
    with open('settlementsInGermany.csv', 'rb') as csvfile:
        cityreader = csv.reader(csvfile, delimiter=',')
    
        cities = []
    
        for row in cityreader:
            #First column is word to look for, second is original city name
            newname = row[0].lower()
            newname = findLcGermanCharsAndReplace(newname)
            cityToAdd = dict()
            cityToAdd['shortname'] = row[0].lower()
            cityToAdd['shortnamePadded'] = ' ' + cityToAdd['shortname'] + ' '
            cityToAdd['originalname'] = row[1]
            cityToAdd['land'] = row[2]
            cities.append(cityToAdd)
            if newname != row[0].lower():
                newCity = cityToAdd.copy()
                newCity['shortname'] = newname
                newCity['shortnamePadded'] = ' ' + newCity['shortname'] + ' '
                cities.append(newCity)
                
        return cities
        
def filterCitiesByLand(cities, land):
    citiesreturned = []
    for city in cities:
        if city['land'] == land:
            citiesreturned.append(city)
    return citiesreturned

#Things that are banned everywhere (except emails, different kind of search)
#Used for tags
banlevel1 = ('konstanz', 'boden', 'wald', 'nusse', 'fisch', 'berge', 'wiesen', 'heide', 'loehne', u'löhne', 'bruecken', u'brücken', 'lichtenberg')

#More things that are banned everywhere (except tags)
#Used for titles
banlevel2 = list(banlevel1)
banlevel2.extend(['sylt', 'jade', 'erden', 'gering', 'balje', 'breit', 'auen', 'stelle', 'ohne', 'bescheid', 'lage', 'muessen', u'müssen', 'steinen', 'schutz', 'elbe', 'fahren', 'plate', 'wellen'])
banlevel2 = tuple(banlevel2)

#More things that are banned everywhere (except titles)
#Used for notes, contact points
banlevel3 = list(banlevel2)
banlevel3.extend(['norden', 'list'])
banlevel3 = tuple(banlevel3)

#Finally some things that are bad in email addresses
#au is in bau, and haus and goodness knows what else
#stelle is in poststelle and handled specially (below)
baninemails = ('stein', 'au', 'bunde')

#Try to get data that relates to a 'city'
def findOnlyCityData(data, cities):
    
    foundItems = []

    for item in data:
        founditem = False
        foundcity = None
        matchedon = ''    
        if ('maintainer' in item and item['maintainer'] != None):
            searchtext = createwholelcwords(item['maintainer'])
            for city in cities:
                if city['shortname'] not in banlevel3 and city['shortnamePadded'] in searchtext:
                        print 'Found in maintainer: ' + city['shortname'] + '\nin\n' + searchtext
                        founditem = True
                        foundcity = city
                        matchedon = 'maintainer'
                        break
        if ((not founditem) and 'author' in item and item['author'] != None):
            searchtext = createwholelcwords(item['author'])
            for city in cities:
                if city['shortname'] not in banlevel3 and city['shortnamePadded'] in searchtext:
                    print 'Found in author: ' + city['shortname'] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city
                    matchedon = 'author'
                    break
        if ((not founditem) and 'maintainer_email' in item and item['maintainer_email'] != None):
            for city in cities:
                if testnospacematch(city['shortname'], extract_em_domain(item['maintainer_email'])):
                    print 'Found in maintainer email domain: ' + city['shortname'] + '\nin\n' + item['maintainer_email'].lower()
                    founditem = True
                    foundcity = city
                    matchedon = 'maintainer_email'
                    break
        if ((not founditem) and 'author_email' in item and item['author_email'] != None):
            for city in cities:
                if testnospacematch(city['shortname'], extract_em_domain(item['author_email'])):
                    print 'Found in author email domain: ' + city['shortname'] + '\nin\n' + item['author_email'].lower()
                    founditem = True
                    foundcity = city
                    matchedon = 'author_email'
                    break
        if ((not founditem) and 'title' in item and item['title'] != None):
            searchtext = createwholelcwords(item['title'])
            for city in cities:
                if city['shortname'] not in banlevel2 and city['shortnamePadded'] in searchtext:
                    print 'Found in title: ' + city['shortname'] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city
                    matchedon = 'title'
                    break
        if ((not founditem) and 'notes' in item and item['notes'] != None):
            searchtext = createwholelcwords(item['notes'])
            for city in cities:
                if city['shortname'] not in banlevel3 and city['shortnamePadded'] in searchtext:
                    print 'Found in notes: ' + city['shortname'] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city
                    matchedon = 'notes'
                    break
        if ((not founditem) and 'tags' in item and len(item['tags']) != 0):
            for city in cities:
                if (founditem):
                    break 
                for tag in item['tags']:
                    #Tag must be exact match
                    if city['shortname'] == tag.lower() and tag.lower() not in banlevel1:
                        print 'Matched tag: ' + city['shortname'] + '\nin\n' + tag.lower()
                        founditem = True
                        foundcity = city
                        matchedon = 'tags'
                        break
        if founditem:
            recordtoadd = dict()
            recordtoadd['item'] = item
            recordtoadd['city'] = foundcity
            recordtoadd['match'] = matchedon
            foundItems.append(recordtoadd)
            
    return foundItems

#There are times when we need to test for city names without expecting whole words, like
#email addresses. But then we really have to rule out a few things. Stein, Au and Bunde are always
#ignored, and stelle (the city) must not be matched against the word poststelle.
def testnospacematch(cityname, searchtext):
    return (not any(x in cityname for x in baninemails) and 
            not ('poststelle' in searchtext.lower() and cityname == 'stelle') and 
            cityname in searchtext.lower())

# City names can be found in all sorts of places, but they shouldn't be found as parts of 
# words. Therefore a good test is to see if they appear as whole words. A simple test for 
# whole words is to see if the word is surrounded by spaces. This function reduces other
# separating items to spaces as a pre-processing step. In case the city might be mentioned
# at the very beginning, we add a space at the beginning, ditto at the end.
def createwholelcwords(words):
    return ' ' + words.replace(',', ' ').replace('.', ' ').replace('\n', ' ').lower() + ' '

### End city names database and cleaning ###
    
### Categories ###
def setBlankCategories(row):
    row[u'Veröffentlichende Stelle'] = ''
    row[u'Arbeitsmarkt'] = ''
    row[u'Bevölkerung'] = ''
    row[u'Bildung und Wissenschaft'] = ''
    row[u'Haushalt und Steuern'] = ''
    row[u'Stadtentwicklung und Bebauung'] = ''
    row[u'Wohnen und Immobilien'] = ''
    row[u'Sozialleistungen'] = ''
    row[u'Öffentl. Sicherheit'] = ''
    row[u'Gesundheit'] = ''
    row[u'Kunst und Kultur'] = ''
    row[u'Land- und Forstwirtschaft'] = ''
    row[u'Sport und Freizeit'] = ''
    row[u'Umwelt'] = ''
    row[u'Transport und Verkehr'] = ''
    row[u'Energie, Ver- und Entsorgung'] = ''
    row[u'Politik und Wahlen'] = ''
    row[u'Gesetze und Justiz'] = ''
    row[u'Wirtschaft und Wirtschaftsförderung'] = ''
    row[u'Tourismus'] = ''
    row[u'Verbraucher'] = ''
    row[u'Sonstiges'] = ''
    row[u'Noch nicht kategorisiert'] = 'x'
    
    return row

def govDataLongToODM(group):
    group = group.strip()
    if group == u'Bevölkerung' or group == u'Bildung und Wissenschaft' or group == u'Gesundheit' or group == u'Transport und Verkehr' or group == u'Politik und Wahlen' or group == u'Gesetze und Justiz':
        return [group]
    elif group == u'Wirtschaft und Arbeit':
        return [u'Arbeitsmarkt', u'Wirtschaft und Wirtschaftsförderung']
    elif u'Verwaltung, Haushalt und Steuern' in group:
        return [u'Haushalt und Steuern', u'Sonstiges']
    elif group == u'Infrastruktur, Bauen und Wohnen':
        return [u'Wohnen und Immobilien', u'Stadtentwicklung und Bebauung']
    elif u'Geologie' in group:
        return [u'Stadtentwicklung und Bebauung']
    elif group == u'Soziales':
        return [u'Sozialleistungen']
    elif u'Sport und Tourismus' in group:
        return [u'Kunst und Kultur', u'Sport und Freizeit', u'Tourismus']
    elif group == u'Umwelt und Klima':
        return [u'Umwelt']
    elif group == u'Verbraucherschutz':
        return [u'Verbraucher']
    else:
        print 'Warning: could not return a category for ' + group
        return []
        
def govDataShortToODM(group):
    group = group.strip()
    if group == 'bevoelkerung' or group == 'society':
        return [u'Bevölkerung']
    elif group == 'bildung_wissenschaft':
        return [u'Bildung und Wissenschaft']
    elif group == 'wirtschaft_arbeit':
        return [u'Arbeitsmarkt', u'Wirtschaft und Wirtschaftsförderung']
    elif group == 'infrastruktur_bauen_wohnen':
        return [u'Wohnen und Immobilien', u'Stadtentwicklung und Bebauung']
    elif group == 'geo' or group == 'structure' or group == 'boundaries' or group == 'gdi-rp':
        return [u'Stadtentwicklung und Bebauung']
    elif group == 'gesundheit' or group == 'health':
        return [u'Gesundheit']
    elif group == 'soziales':
        return [u'Sozialleistungen']
    elif group == 'kultur_freizeit_sport_tourismus':
        return [u'Kunst und Kultur', u'Sport und Freizeit', u'Tourismus']
    elif group == 'umwelt_klima' or group == 'environment' or group == 'biota' or group == 'oceans':
        return [u'Umwelt']
    elif group == 'transport_verkehr':
        return [u'Transport und Verkehr']
    elif group == 'verbraucher':
        return [u'Verbraucher']
    elif group == 'politik_wahlen':
        return [u'Politik und Wahlen']
    elif group == 'gesetze_justiz':
        return [u'Gesetze und Justiz']
    elif group == 'economy':
        return [u'Wirtschaft und Wirtschaftsförderung']
    elif group == 'verwaltung':
        return [u'Sonstiges']
    else:
        print 'Warning: could not return a category for ' + group
        return []
### End Categories ###          
