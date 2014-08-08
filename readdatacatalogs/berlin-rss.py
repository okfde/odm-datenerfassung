import unicodecsv as csv
import time
import urllib
import xml.etree.ElementTree as etree
from lxml import html
import sys

csvoutfile = open(sys.argv[1]+'.csv', 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')

csv_file_files = open(sys.argv[1]+'.files.csv', 'wb')
filesdatawriter = csv.writer(csv_file_files, delimiter=',')

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
    url = item.find('link').text
    row.append(url)
    datawriter.writerow(row)
    
    print u'Reading ' + url
    try:
        datapage = html.parse(url)
    except:
        print u'WARNING: Could not download ' + url
        continue
    
    links = datapage.xpath('//div[contains(@class, "field-name-field-url")]//a/@href')
            
    print str(len(links)) + ' resources found'
    
    if len(links) == 0:
        links = datapage.xpath('//div[contains(@class, "field-name-field-website")]//a/@href')
    
    for link in links:
        print 'Writing link: ' + link
        filerow = []
        filerow.append(link)
        filesdatawriter.writerow(filerow)    
        
csvoutfile.close();