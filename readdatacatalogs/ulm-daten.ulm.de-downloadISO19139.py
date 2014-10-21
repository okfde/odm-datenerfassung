import unicodecsv
import urllib2
import urllib
import codecs

from lxml import html
from lxml import etree
from lxml.etree import LxmlError

root = u'http://daten.ulm.de'
startUrl = root + u'/suche?search_api_views_fulltext='
page = 0

giantxml = []

dataCount = -1

#Output the list of files for analysis
csv_file = codecs.open('../metadata/ulm/catalogfiles.csv', 'w', 'utf-8')

while True:
    if dataCount == 0:
        print u'INFO: Search page contained no results, stopping.'
        #Done
        break
    
    if dataCount != -1:
        print u'INFO: Search page contained ' + str(dataCount) + ' results, ' + str(len(giantxml)) + ' datasets downloaded so far'

    dataCount = 0

    searchurl = startUrl + '&page=' + str(page)
    print u'Reading search page ' + searchurl
    data = html.parse(searchurl)
    
    page += 1
    
    sites = data.xpath('//body//a')
    
    for site in sites:
        if len(site.xpath('@href')) > 0:
            dataurl =  site.xpath('@href')[0]
        else:
            continue
        
        if ('/daten/' in dataurl) or ('/datenkatalog/' in dataurl):
            dataCount += 1
            #Not all data records contain actual files; geo services have a download form
            filenameFound = False
            #It would be nice if this gave us the node id, and then we could just
            #call the XML link directly. But its an alias, so to find the actual node
            #id/link for XML (which doesn't work with aliases), we have to look at the page,
            #the link to the XML is a good place to start; it is relative so in the end we still
            #create the link ourselves.
            dataurl = root + dataurl
            
            print u'Reading dataset page ' + dataurl
            try:
                datapage = html.parse(dataurl)
            except:
                print u'WARNING: Could not download ' + dataurl
                continue
                
            links = datapage.xpath('//body//a')
            
            for link in links:
                if len(link.xpath('@href')) > 0:
                    linkurl =  link.xpath('@href')[0]
                else:
                    continue

                #The dataurl although containing ascii-safe text is actually unicoded
                #First produce an ascii-coded string that we can then decode into unicode
                unquotedurl = urllib.unquote(dataurl.encode('ASCII')).decode('utf8')
                
                #Get files... they are not listed in the XML...!
                #Seems that link files have a nice type attribute
                if len(link.xpath('@type')) > 0:
                    filenamefound = True
                    print 'Found file: ' + link.xpath('@href')[0]
                    csv_file.write(unquotedurl  + ',file,' + link.xpath('@href')[0] + '\n')
                #Find the license, also not in XML  
                if len(link.xpath('@rel')) > 0 and link.xpath('@rel')[0] == 'license' and link.text is not None:
                    licenseFound = True
                    print 'Found license: ' + link.text
                    csv_file.write(unquotedurl  + ',license,' + link.text + '\n')
                #Find the metadata XML    
                if ('/iso19139/' in linkurl):
                    node = linkurl.split('/')[-1]
                    xmlurl = root + u'/datenkatalog/iso19139/' + node
                    print u'Downloading XML from ' + xmlurl
                    
                    response = urllib2.urlopen(xmlurl)
                    xml = unicode(response.read(), 'utf-8')
                    giantxml.append(xml)
    
print 'Done. Found ' + str(len(giantxml)) + ' files'
finalstring = u'\n'.join([xml for xml in giantxml])
#currently, the portal puts '&' in URLs... bad
finalstring = finalstring.replace('&', '&amp;')

csv_file.close()

with codecs.open('../metadata/ulm/catalog.xml', 'w', 'utf-8') as xml_file:
    #Needed for valid xml
    xml_file.write(u'<xml>\n')
    xml_file.write(finalstring)
    xml_file.write(u'</xml>')
