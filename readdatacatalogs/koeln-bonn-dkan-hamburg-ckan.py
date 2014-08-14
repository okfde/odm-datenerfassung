import urllib, json
import unicodecsv as csv
import sys

url = ""
if sys.argv[1] == "koeln":
    url = "http://offenedaten-koeln.de"
elif sys.argv[1] == "bonn":
    url = "http://opendata.bonn.de"
elif sys.argv[1] == "hamburg":
    url = "http://opendata.hamburg.de"

if sys.argv[1] == "hamburg":
    jsonurl = urllib.urlopen(url + "/api/3/action/package_list?limit=10000")
    listpackages = json.loads(jsonurl.read())
    listpackages = listpackages['result']
    groups = []
    for item in listpackages:
        print 'Downloading dataset ' + item
        purl = urllib.urlopen(url + "/api/3/action/package_show?id=" + item)
        pdata = json.loads(purl.read())
        groups.append(pdata['result'])
else:
    jsonurl = urllib.urlopen(url + "/api/3/action/current_package_list_with_resources")
    groups = json.loads(jsonurl.read())

csvoutfile = open(sys.argv[2]+'.csv', 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')
csv_files = open(sys.argv[2]+'.files.csv', 'wb')
csv_files_writer = csv.writer(csv_files, delimiter=',')

columns = [ 'title', 'description', 'keyword', 'modified', 'publisher', 'person', 'mbox', 'identifier', 'accessLevel', 'accessURL', 'webService', 'license', 'spatial', 'temporal', 'language', 'granularity']

row = []
for column in columns:
    row.append(column);

datawriter.writerow(row)

for package in groups:
    filefound = False
    #Get files for analysis
    fulljsonurl = urllib.urlopen(package['webService'])
    fulldata = json.loads(fulljsonurl.read())
    
    if ('resources' in fulldata):
        for file in fulldata['resources']:
            if (file['file_url'] != ''):
                filefound = True
                filerow = []
                filerow.append(file['file_url'])
                csv_files_writer.writerow(filerow)
    
    if not filefound:
        filerow = []
        #Fake file for analysis
        filerow.append('/' + package['identifier'])
        csv_files_writer.writerow(filerow)

    row = []
    for column in columns:
        row.append(package[column])
    datawriter.writerow(row)

csvoutfile.close()
csv_files.close()

