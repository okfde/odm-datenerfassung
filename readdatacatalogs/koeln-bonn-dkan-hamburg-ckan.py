import urllib, json
import unicodecsv as csv
import sys

import metautils

def dequotejson(stringvalue):
    cleanvalue = stringvalue.replace('\\', '')
    cleanvalue = cleanvalue[1:len(cleanvalue)-1]
    return cleanvalue
    
actualcategories = []

url = ""
if sys.argv[1] == "koeln":
    url = "http://offenedaten-koeln.de"
elif sys.argv[1] == "bonn":
    url = "http://opendata.bonn.de"
elif sys.argv[1] == "hamburg":
    url = "http://opendata.hamburg.de"

if sys.argv[1] == "hamburg":
    jsonurl = urllib.urlopen(url + "/api/3/action/package_list?limit=10000")
    if len(sys.argv) > 3:
        print 'Loading from file...'
        jsonurl = open(sys.argv[3], 'rb')
    listpackages = json.loads(jsonurl.read())
    if len(sys.argv) < 3:
        listpackages = listpackages['result']
    if len(sys.argv) > 3:
        jsonurl.close()
    groups = []
    if len(sys.argv) < 3:
        for item in listpackages:
            print 'Downloading dataset ' + item
            purl = urllib.urlopen(url + "/api/3/action/package_show?id=" + item)
            pdata = json.loads(purl.read())
            groups.append(pdata['result'])
    else:
        groups = listpackages
else:
    jsonurl = urllib.urlopen(url + "/api/3/action/current_package_list_with_resources")
    groups = json.loads(jsonurl.read())

#It takes a long time to gather the Hamburg data... save it
if sys.argv[1] == "hamburg":
    with open('hamburgdump.json', 'wb') as outfile:
        json.dump(groups, outfile)

csvoutfile = open(sys.argv[2]+'.csv', 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')
csv_files = open(sys.argv[2]+'.files.csv', 'wb')
csv_files_writer = csv.writer(csv_files, delimiter=',')

if sys.argv[1] != "hamburg":
    columns = [ 'title', 'description', 'notes', 'keyword', 'modified', 'publisher', 'person', 'mbox', 'identifier', 'accessLevel', 'accessURL', 'webService', 'license', 'spatial', 'temporal', 'language', 'granularity']
    inextras = []
else:
    columns = ['id', 'name', 'notes', 'title', 'tags', 'groups', 'isopen', 'url', 'license_id', 'license_title', 'maintainer', 'metadata_created', 'metadata_modified', 'author', 'state', 'version', 'type']
    inextras = ['geographical_granularity', 'metadata_original_portal', 'metadata_original_xml', 'ogd_version', 'sector', 'spatial-text', 'subgroups']

    possibledates = []

    #Simplification!
    if sys.argv[1] == "hamburg":
        for hitem in groups:
            simplifiedextras = dict()
            for extra in hitem['extras']:
                if extra['key'] == 'dates':
                    cleanvalue = dequotejson(extra['value'])
                    jsondate = json.loads(cleanvalue)
                    if jsondate[0]['role'] not in possibledates:
                        possibledates.append(jsondate[0]['role'])
                    simplifiedextras[jsondate[0]['role']] = jsondate[0]['date']
                elif extra['key'] == 'subgroups':
                    cleanvalue = dequotejson(extra['value'])
                    arrayofgroups = json.loads(cleanvalue)
                    simplifiedextras['subgroups'] = metautils.arraytocsv(arrayofgroups)
                else:
                    simplifiedextras[extra['key']] = extra['value'].replace('"', '')
            hitem['extras'] = simplifiedextras
                
    inextras.extend(possibledates)
    columns.extend(inextras)
                
row = []
for column in columns:
    row.append(column);

datawriter.writerow(row)

for package in groups:
    filefound = False
    
    resources = []
    thekey = 'url'
    
    if sys.argv[1] != "hamburg":
        fulljsonurl = urllib.urlopen(package['webService'])
        fulldata = json.loads(fulljsonurl.read())
        thekey = 'file_url'
        if ('resources' in fulldata):
            resources = fulldata['resources']
    else:
        if ('resources' in package):
            resources = package['resources']
    
    for file in resources:
        if (file[thekey] != ''):
            filefound = True
            filerow = []
            filerow.append(file[thekey])
            csv_files_writer.writerow(filerow)
    
    if not filefound:
        filerow = []
        #Fake file for analysis
        filerow.append('/' + package['identifier'])
        csv_files_writer.writerow(filerow)

    row = []
    for column in columns:
        if column == 'tags':
            row.append(metautils.setofvaluesascsv(package['tags'], 'display_name'))
        elif column == 'groups':
            row.append(metautils.setofvaluesascsv(package['groups'], 'title'))
            arrayofcats = metautils.setofvaluesasarray(package['groups'], 'title')
            for part in arrayofcats:
                if part not in actualcategories:
                    actualcategories.append(part)
        elif column in inextras:
            if column in package['extras']:
                row.append(package['extras'][column])
            else:
                row.append('')
        elif column in package:
            row.append(package[column])
        else:
            row.append('')
    datawriter.writerow(row)

csvoutfile.close()
csv_files.close()

print 'Final list of categories: ' + metautils.arraytocsv(actualcategories)

