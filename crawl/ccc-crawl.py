import sys
import unicodecsv as csv
from lxml import etree

#TODO: also in other crawlers, also cover mime types (. will be removed!)
filetypes = ['.CSV', '.XLS', '.XLSX', '.JSON', '.RDF', '.ZIP', '.EXCEL'] 
geofiletypes = ('.GEOJSON', '.GML', '.GPX', '.GJSON', '.TIFF', '.SHP', '.KML', '.KMZ', '.WMS', '.WFS')
filetypes.extend(geofiletypes)
filetypes = tuple(filetypes)

csvoutfile = open(sys.argv[1]+'.data.csv', 'a+b')
datawriter = csv.writer(csvoutfile, delimiter=',')

columns = ['Stadt_URL', 'URL_Datei', 'URL_Text', 'URL_Dateiname', 'Format', 'geo', 'URL_PARENT', 'Title_Parent']

datawriter.writerow(columns)

with open(sys.argv[2], 'rb') as archive:
  domain = sys.argv[1]
  blacklist = ('.jpg', '.gif', '.ico', '.txt', '.pdf', '.png', 'dns:', '.css', '.js')
  
  records = archive.read().split("\nhttp://")
  
  print 'File contains ' + str(len(records)) + ' pages' 
  
  for record in records:
      info = record.split('\n')
      contenttype = ""
      parent = 'http://' + info[0].split(' ')[0]
      filename = parent.split('/')[-1]
      
      if domain not in parent:
          continue
      
      isafile = False
      
      for line in info:
          if 'Content-Type' in line:
              contenttype = line
              
      for ext in filetypes:
          if (ext[1:] in contenttype.upper()) or (ext[1:] in filename.upper()):
              print "Detected a downloadable file"
              geo = ''
              if (ext in geofiletypes):
                  geo = 'x'
              copout = u'Nicht moeglich kann aber nachtraeglich ermittelt werden'
              row = [sys.argv[1],parent,'',filename,ext[1:],geo,copout,copout]
              datawriter.writerow(row)
              isafile = True
              break
      
      if isafile:
          continue
      
      if 'html' in contenttype:
          try:
              page = record.split('<html')[1]

              page = '<html' + page      
              htmldata = etree.HTML(page)
          
              #TODO, see if some of this can be packed into a class
              #Title of the page we are on (this will be the 'parent')
              parent_title = ''
              if len(htmldata.xpath('//title/text()')) > 0:
                  parent_title = htmldata.xpath('//title/text()')[0]

              #URL of the page we are on (parent)
              parent_url = parent
        
              #Get all links
              sites = htmldata.xpath('//body//a')

              for site in sites:
                  URL_Datei = unicode('', 'utf-8')
                  if len(site.xpath('@href')) > 0:
                      URL_Datei  = site.xpath('@href')[0]
                  else:
                      continue
            
                  Stadt_URL = unicode(sys.argv[1], 'utf-8')
            
                  #Get ALL text of everything inside the link
                  #First any sub-elements like <span>
                  textbits = site.xpath('child::node()')
                  URL_Text = unicode('', 'utf-8')
                  for text in textbits:
                      try:
                          if (len(text) > 0): URL_Text += text
                      except:
                          if len(text.xpath('text()')) > 0:
                              URL_Text += text.xpath('text()')[0]
                  #Then the actual text
                  directText = ''
                  if len(site.xpath('text()')) > 0:
                      directText = site.xpath('text()')[0]
                  
                  #If there's something there and it isn't a repetition, use it
                  if (len(directText) > 0) and (directText != URL_Text):
                      URL_Text += directText
                  URL_Text = URL_Text.replace("\t", " ").replace("\n", "").strip()
            
                  #If that got us nothing, then look at the title and alt elements
                  title_text = ''
                  if len(site.xpath('@title')) > 0:
                      title_text = site.xpath('@title')[0]

                  if (len(title_text)>0) and (URL_Text == u''):
                      URL_Text = title_text
                  
                  alt_text = ''
                  if len(site.xpath('@alt')) > 0:
                      alt_text = site.xpath('@alt')[0]
                  if (len(alt_text)>0) and (URL_Text == u''):
                      URL_Text = alt_text
            
                  URL_Dateiname = unicode(URL_Datei).split('/')[-1]
                  Format = u'Not interesting'
                  geo = u''
                  URL_PARENT = parent_url
                  Title_PARENT = parent_title
            
                  #Is it a file (does it have any of the extensions (including the '.' in the filename,
                  #then remove the '.' 
                  for ext in filetypes:
                      if ext in URL_Datei.encode('ascii', errors='ignore').upper():
                         Format = ext[1:len(ext)]
                         #And is it one of our special geo filetypes?
                         if ext in geofiletypes:
                             geo = 'x'
                         row = [Stadt_URL, URL_Datei, URL_Text, URL_Dateiname, Format, geo, URL_PARENT, Title_PARENT]
                         datawriter.writerow(row)
          except:
              print 'Couldn\'t parse: \n' + record

csvoutfile.close()
