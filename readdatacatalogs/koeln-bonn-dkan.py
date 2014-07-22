import urllib, json
import unicodecsv as csv
import sys

url = ""
if sys.argv[1] == "koeln":
    url = "http://offenedaten-koeln.de"
elif sys.argv[1] == "bonn":
    url = "http://opendata.bonn.de"

jsonurl = urllib.urlopen(url + "/api/3/action/current_package_list_with_resources")
groups = json.loads(jsonurl.read())

csvoutfile = open(sys.argv[2], 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')

columns = [ 'title', 'description', 'keyword', 'modified', 'publisher', 'person', 'mbox', 'identifier', 'accessLevel', 'accessURL', 'webService', 'license', 'spatial', 'temporal', 'language', 'granularity']

row = []
for column in columns:
    row.append(column);

datawriter.writerow(row)

for package in groups:
    row = []
    for column in columns:
        row.append(package[column])
    datawriter.writerow(row)

csvoutfile.close()

