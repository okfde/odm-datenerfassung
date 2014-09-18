# -*- coding: utf-8 -*-
import sys
import json
import codecs
import unicodecsv as csv

import metautils

actualcategories = []

if (len(sys.argv)<3):
    print 'Usage: datagov-ckan-getDataFromSettlements datagovJSONDump.json outputFile.csv'
    exit()

excludes = []

if (len(sys.argv)>3):
    excludes = sys.argv[3].split(',')
    print 'Excluding following portals:'
    for portal in excludes:
        print portal
        
cities = metautils.getCities()

with open(sys.argv[1], 'rb') as jsonfile:
    text = jsonfile.read()
    data = json.loads(text)

foundItems = metautils.findOnlyCityData(data, cities)

print 'Out of ' + str(len(data)) + ' catalog entries, ' + str(len(foundItems)) + ' appear to be related to the input list of settlements'

print 'Writing CSV file...'

columns = ['city', 'matched_on', 'title', 'notes', 'tags', 'groups', 'format', 'geo', 'metadata_modified', 'author', 'author_email', 'maintainer', 'maintainer_email', 'id', 'url', 'license', 'isopen']
inextras = ('metadata_original_portal', 'temporal_coverage_to', 'temporal_coverage_from', 'metadata_modified', 'metadata_created')
columns.extend(inextras)

mopIndex = columns.index('metadata_original_portal')
excludecount = 0

with open(sys.argv[2], 'wb') as csvoutfile:
    datawriter = csv.writer(csvoutfile, delimiter=',')

    row = []
    for column in columns:
        row.append(column);

    datawriter.writerow(row)

    for foundItem in foundItems:
        item = foundItem['item']
        matchedon = foundItem['match']
        thecity = foundItem['city']
         
        row = []
        geo = ''
        for column in columns:
            if column == 'city':
                row.append(thecity)
            elif column == 'matched_on':
                row.append(matchedon)
            elif column == 'groups' or column == 'tags':
                row.append(metautils.getgroupofelements(column, item))
                if column == 'groups':
                    for part in item[column]:
                        if part not in actualcategories:
                            actualcategories.append(part)
            elif column == 'url':
                row.append('https://www.govdata.de/daten/-/details/' + item['id'])
            elif column == 'format':
                formatstring = ''
                if 'resources' in item:
                    for resource in item['resources']:
                        formatstring += resource['format'] + ','
                        if resource['format'].upper() in metautils.geoformats:
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
                    row.append('')
            elif column in item:
                row.append(item[column])
            else:
                row.append('')
        print len(row)
        print mopIndex
        if not any(x in row[mopIndex] for x in excludes):
            datawriter.writerow(row)
        else:
            print 'Not writing entry, in excludes list'
            excludecount += 1

print str(excludecount) + ' items excluded.'
print 'Final list of categories: ' + metautils.arraytocsv(actualcategories)
