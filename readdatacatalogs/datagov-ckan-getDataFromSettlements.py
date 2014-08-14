# -*- coding: utf-8 -*-
import sys
import json
import codecs
import unicodecsv as csv

def createwholelcwords(words):
    return words.replace(',', ' ').replace('.', ' ').replace('\n', ' ').lower()
    
def testnospacematch(cityname, searchtext):
    #au is in bau, and haus and goodness knows what else
    #stelle is in poststelle
    sillycities = ('stein', 'au')
    return (not any(x in cityname for x in sillycities) and 
            not ('poststelle' in searchtext.lower() and cityname == 'stelle') and 
            cityname in searchtext.lower())

#This word comes up a lot
reallysillycities = ('stelle')

geoformats = ('GEOJSON', 'GML', 'GPX', 'GJSON', 'TIFF', 'SHP', 'KML', 'KMZ', 'WMS', 'WFS', 'GML2', 'GML3', 'SHAPE')

if (len(sys.argv)<4):
    print 'Usage: datagov-ckan-getDataFromSettlements inputListOfCities.csv datagovJSONDump.json outputFile.csv'
    exit()

with open(sys.argv[1], 'rb') as csvfile:
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
        cities.append([row[0].lower(), row[1]])
        if newname != row[0].lower():
            newrow = [newname, row[1]]
            cities.append(newrow)

with open(sys.argv[2], 'rb') as jsonfile:
    text = jsonfile.read()
    data = json.loads(text)   
    
    foundItems = []
    foundCities = []
    matches = []

    for item in data:
        founditem = False
        foundcity = ''
        matchedon = ''
        
        if ('maintainer' in item and item['maintainer'] != None):
            searchtext = createwholelcwords(item['maintainer'])
            for city in cities:
                if city[0] not in reallysillycities and (' ' + city[0] + ' ') in searchtext:
                    print 'Found in maintainer: ' + city[0] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city[1]
                    matchedon = 'maintainer'
                    break
        if ((not founditem) and 'author' in item and item['author'] != None):
            searchtext = createwholelcwords(item['author'])
            for city in cities:
                if city[0] not in reallysillycities and (' ' + city[0] + ' ') in searchtext:
                    print 'Found in author: ' + city[0] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city[1]
                    matchedon = 'author'
                    break
        if ((not founditem) and 'maintainer_email' in item and item['maintainer_email'] != None):
            for city in cities:
                if city[0] not in reallysillycities and testnospacematch(city[0], item['maintainer_email']):
                    print 'Found in maintainer email: ' + city[0] + '\nin\n' + item['maintainer_email'].lower()
                    founditem = True
                    foundcity = city[1]
                    matchedon = 'maintainer_email'
                    break
        if ((not founditem) and 'author_email' in item and item['author_email'] != None):
            for city in cities:
                if city[0] not in reallysillycities and testnospacematch(city[0], item['author_email']):
                    print 'Found in author email: ' + city[0] + '\nin\n' + item['author_email'].lower()
                    founditem = True
                    foundcity = city[1]
                    matchedon = 'author_email'
                    break
        if ((not founditem) and 'notes' in item and item['notes'] != None):
            searchtext = createwholelcwords(item['notes'])
            for city in cities:
                if city[0] not in reallysillycities and (' ' + city[0] + ' ') in searchtext:
                    print 'Found in notes: ' + city[0] + '\nin\n' + searchtext
                    founditem = True
                    foundcity = city[1]
                    matchedon = 'notes'
                    break
        #For this, we allow stelle, as stelle as a single tag would be silly
        if ((not founditem) and 'tags' in item and len(item['tags']) != 0):
            for city in cities:
                if (founditem):
                    break 
                for tag in item['tags']:
                    #Tag must be exact match
                    if city[0] == tag.lower():
                        print 'Matched tag: ' + city[0] + '\nin\n' + tag.lower()
                        founditem = True
                        foundcity = city[1]
                        matchedon = 'tags'
                        break
        if founditem:
            foundItems.append(item)
            foundCities.append(foundcity)
            matches.append(matchedon)

jsonfile.close()

print 'Out of ' + str(len(data)) + ' catalog entries, ' + str(len(foundItems)) + ' appear to be related to the input list of settlements'

print 'Writing CSV file...'

columns = ['city', 'matched_on', 'title', 'notes', 'tags', 'format', 'geo', 'metadata_modified', 'author', 'author_email', 'maintainer', 'maintainer_email', 'id', 'url', 'license', 'isopen', 'metadata_original_portal', 'temporal_coverage_to', 'temporal_coverage_from', 'metadata_modified', 'metadata_created']
inextras = ('metadata_original_portal', 'temporal_coverage_to', 'temporal_coverage_from', 'metadata_modified', 'metadata_created')
with open(sys.argv[3], 'wb') as csvoutfile:
    datawriter = csv.writer(csvoutfile, delimiter=',')

    row = []
    for column in columns:
        row.append(column);

    datawriter.writerow(row)

    count = -1;

    for item in foundItems:
        count += 1
        row = []
        geo = ''
        for column in columns:
            if column == 'city':
                row.append(foundCities[count])
            elif column == 'matched_on':
                row.append(matches[count])
            elif column == 'tags':
                tagstring = ''
                for tag in item['tags']:
                    tagstring += tag + ','
                #Get rid of last commas
                tagstring = tagstring[0:len(tagstring)-1]
                row.append(tagstring)
            elif column == 'url':
                row.append('https://www.govdata.de/daten/-/details/' + item['id'])
            elif column == 'format':
                formatstring = ''
                if 'resources' in item:
                    for resource in item['resources']:
                        formatstring += resource['format'] + ','
                        if resource['format'].upper() in geoformats:
                            geo = 'x'
                    #Get rid of last commas
                    formatstring = formatstring[0:len(formatstring)-1]
                row.append(formatstring)
            elif column == 'geo':
                row.append(geo)
            elif column in inextras:
                if column in item['extras']:
                    row.append(item['extras'][column])
            else:
                row.append(item[column])
        datawriter.writerow(row)
