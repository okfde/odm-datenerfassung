# -*- coding: utf-8 -*-
import unicodecsv as csv

### Interesting formats ###
geoformats = ('GEOJSON', 'GML', 'GPX', 'GJSON', 'TIFF', 'SHP', 'KML', 'KMZ', 'WMS', 'WFS', 'GML2', 'GML3', 'SHAPE')

#TODO: Define mime types also

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
    
### End Dealing with data structures ###

### Data processing utilities ###
def extractFormat(filestring):
    return "PASS"
### End data processing utilities ###

### City names database and cleaning ###
def getCities():
    with open('settlementsInGermany.csv', 'rb') as csvfile:
        cityreader = csv.reader(csvfile, delimiter=',')
    
        cities = []
    
        for row in cityreader:
            #First column is word to look for, second is original city name
            germanchars = (u'ü',u'ä',u'ö',u'é',u'ß')
            englishreplacements = ('ue', 'ae', 'oe', 'ee', 'ss')
            newname = row[0].lower()
            for x in range(0,len(germanchars)):
                if germanchars[x] in row[0]:
                    newname = newname.replace(germanchars[x], englishreplacements[x])
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

#Try to get data that relates to a 'city'
def findOnlyCityData(data, cities):
    
    foundItems = []

    for item in data:
        founditem = False
        foundcity = ''
        matchedon = ''    
        if ('maintainer' in item and item['maintainer'] != None):
            searchtext = createwholelcwords(item['maintainer'])
            for city in cities:
                if city['shortname'] not in reallysillycities and city['shortnamePadded'] in searchtext:
                    print 'Found in maintainer: ' + city['shortname'] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city['originalname']
                    matchedon = 'maintainer'
                    break
        if ((not founditem) and 'author' in item and item['author'] != None):
            searchtext = createwholelcwords(item['author'])
            for city in cities:
                if city['shortname'] not in reallysillycities and city['shortnamePadded'] in searchtext:
                    print 'Found in author: ' + city['shortname'] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city['originalname']
                    matchedon = 'author'
                    break
        if ((not founditem) and 'maintainer_email' in item and item['maintainer_email'] != None):
            for city in cities:
                if city['shortname'] not in reallysillycities and testnospacematch(city['shortname'], item['maintainer_email']):
                    print 'Found in maintainer email: ' + city['shortname'] + '\nin\n' + item['maintainer_email'].lower()
                    founditem = True
                    foundcity = city['originalname']
                    matchedon = 'maintainer_email'
                    break
        if ((not founditem) and 'author_email' in item and item['author_email'] != None):
            for city in cities:
                if city['shortname'] not in reallysillycities and testnospacematch(city['shortname'], item['author_email']):
                    print 'Found in author email: ' + city['shortname'] + '\nin\n' + item['author_email'].lower()
                    founditem = True
                    foundcity = city['originalname']
                    matchedon = 'author_email'
                    break
        if ((not founditem) and 'title' in item and item['title'] != None):
            searchtext = createwholelcwords(item['title'])
            for city in cities:
                if city['shortname'] not in reallysillycities and city['shortnamePadded'] in searchtext:
                    print 'Found in title: ' + city['shortname'] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city['originalname']
                    matchedon = 'title'
                    break
        if ((not founditem) and 'notes' in item and item['notes'] != None):
            searchtext = createwholelcwords(item['notes'])
            for city in cities:
                if city['shortname'] not in reallysillycities and city['shortnamePadded'] in searchtext:
                    print 'Found in notes: ' + city['shortname'] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city['originalname']
                    matchedon = 'notes'
                    break
        #For this, we allow the silly cities, as we would not expect to find them as a single tag
        if ((not founditem) and 'tags' in item and len(item['tags']) != 0):
            for city in cities:
                if (founditem):
                    break 
                for tag in item['tags']:
                    #Tag must be exact match
                    if city['shortname'] == tag.lower():
                        print 'Matched tag: ' + city['shortname'] + '\nin\n' + tag.lower()
                        founditem = True
                        foundcity = city['originalname']
                        matchedon = 'tags'
                        break
        if founditem:
            recordtoadd = dict()
            recordtoadd['item'] = item
            recordtoadd['city'] = foundcity
            recordtoadd['match'] = matchedon
            foundItems.append(recordtoadd)
            
    return foundItems

#These words comes up a lot... they should only be matched against things like tags
reallysillycities = ('stelle', 'ohne')

#There are times when we need to test for city names without expecting whole words, like
#email addresses. But then we really have to rule out a few things. Stein and Au are always
#ignored, and stelle (the city) must not be matched against the word poststelle.
def testnospacematch(cityname, searchtext):
    #au is in bau, and haus and goodness knows what else
    #stelle is in poststelle
    sillycities = ('stein', 'au')
    return (not any(x in cityname for x in sillycities) and 
            not ('poststelle' in searchtext.lower() and cityname == 'stelle') and 
            cityname in searchtext.lower())

# City names can be found in all sorts of places, but they shouldn't be found as parts of 
# words. Therefore a good test is to see if they appear as whole words. A simple test for 
# whole words is to see if the word is surrounded by spaces. This function reduces other
# separating items to spaces as a pre-processing step. In case the city might be mentioned
# at the very beginning, we add a space at the beginning.
def createwholelcwords(words):
    return ' ' + words.replace(',', ' ').replace('.', ' ').replace('\n', ' ').lower()

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
    
def getTargetColumns():
    return [u'Quelle', u'Stadt', u'URL PARENT', u'Dateibezeichnung', u'URL Datei', u'Format', u'Beschreibung', u'Zeitlicher Bezug', u'Lizenz', u'Kosten', u'Veröffentlichende Stelle', u'Arbeitsmarkt', u'Bevölkerung', u'Bildung und Wissenschaft', u'Haushalt und Steuern', u'Stadtentwicklung und Bebauung', u'Wohnen und Immobilien', u'Sozialleistungen', u'Öffentl. Sicherheit', u'Gesundheit', u'Kunst und Kultur', u'Land- und Forstwirtschaft', u'Sport und Freizeit', u'Umwelt', u'Transport und Verkehr', u'Energie, Ver- und Entsorgung', u'Politik und Wahlen', u'Gesetze und Justiz', u'Wirtschaft und Wirtschaftsförderung', u'Tourismus', u'Verbraucher', u'Sonstiges', u'Noch nicht kategorisiert']

def govDataLongToODM(group):
    group = group.strip()
    if group == u'Bevölkerung' or group == u'Bildung und Wissenschaft' or group == u'Gesundheit' or group == u'Transport und Verkehr' or group == u'Politik und Wahlen' or group == u'Gesetze und Justiz':
        return [group]
    elif group == u'Wirtschaft und Arbeit':
        return [u'Arbeitsmarkt', u'Wirtschaft und Wirtschaftsförderung']
    elif group == u'Öffentliche Verwaltung, Haushalt und Steuern':
        return [u'Haushalt und Steuern', u'Sonstiges']
    elif group == u'Infrastruktur, Bauen und Wohnen':
        return [u'Wohnen und Immobilien', u'Stadtentwicklung und Bebauung']
    elif group == u'Infrastruktur, Bauen und Wohnen' or group == u'Geographie, Geologie und Geobasisdaten':
        return [u'Stadtentwicklung und Bebauung']
    elif group == u'Soziales':
        return [u'Sozialleistungen']
    elif group == u'Kultur, Freizeit, Sport und Tourismus':
        return [u'Kunst und Kultur', u'Sport und Freizeit', u'Tourismus']
    elif group == u'Umwelt und Klima':
        return [u'Umwelt']
    elif group == u'Verbraucherschutz':
        return [u'Verbraucher(-schutz)']
    else:
        return []
### End Categories ###          