import unicodecsv as csv
import time
import urllib
import xml.etree.ElementTree as etree
import sys

csvoutfile = open(sys.argv[1], 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')

url = "http://daten.berlin.de/datensaetze/rss.xml"
resp = urllib.urlopen(url)
xml = resp.read()
root = etree.fromstring(xml)
items = root.find("channel").findall("item")

row = ['title', 'description', 'link']

datawriter.writerow(row)

for item in items:
    row = []
    row.append(item.find('title').text)
    row.append(item.find('description').text)
    row.append(item.find('link').text)
    datawriter.writerow(row)
        
csvoutfile.close();