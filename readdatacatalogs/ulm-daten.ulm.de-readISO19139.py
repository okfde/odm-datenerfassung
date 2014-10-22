import unicodecsv as csv
import urllib2
import json

from lxml import objectify

import metautils
from dbsettings import settings

def decrypt_role(role):
    #Based on http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml
    if role == 'resourceProvider':
        return 'Provider'
    elif role == 'custodian':
        return 'Custodian'
    elif role == 'owner':
        return 'Owner'
    elif role == 'user':
        return 'User'
    elif role =='distributor':
        return 'Distributor'
    elif role =='originator':
        return 'Originator'
    elif role =='pointOfContact':
        return 'Point of Contact'
    elif role =='principalInvestigator':
        return 'Principal Investigator'
    elif role =='processor':
        return 'Processor'
    elif role =='publisher':
        return 'Publisher'
    elif role =='author':
        return 'Author'
    else:
        return 'Unbekannt'

#Geographic file types
geofiletypes = ('GEOJSON', 'GML', 'GPX', 'GJSON', 'TIFF', 'SHP', 'KML', 'KMZ', 'WMS', 'WFS', 'GML2', 'GML3', 'SHAPE')

with open('../metadata/ulm/catalog.xml', 'r') as xml_file:
    finalstring = xml_file.read()

#delete later (moved to downloader)
#currently, the portal puts '&' in URLs... bad
finalstring = finalstring.replace('&', '&amp;')

#It seems that lxml has problems with large XML files
#(http://stackoverflow.com/questions/8129329/lxml-iterparse-mising-child-nodes)
#According to that article we can use event-based parsing to solve the problem,
#but we use something less beautiful instead...
finalstring = finalstring.split('<xml>')[1].split('</xml>')[0].strip()
xmlparts = finalstring.split('</gmd:MD_Metadata>')
records = []

ns1 = '{http://www.isotc211.org/2005/gmd}'
ns2 = '{http://www.isotc211.org/2005/gco}'
ns3 = '{http://www.isotc211.org/2005/srv}'
ns4 = '{http://www.opengis.net/gml/3.2}'

for part in xmlparts:
    if part != '':
        record = dict()
      
        part += '</gmd:MD_Metadata>'
        record['xml'] = part
        root = objectify.fromstring(part)
      
        maintainer = root[ns1+'contact'][ns1+'CI_ResponsibleParty']
      
        record['maintainername'] = maintainer[ns1+'individualName'][ns2+'CharacterString'].text
        record['maintainerposition'] = maintainer[ns1+'positionName'][ns2+'CharacterString'].text
        record['maintainerorganisation'] = maintainer[ns1+'organisationName'][ns2+'CharacterString'].text
          
        maintainerContact = maintainer[ns1+'contactInfo'][ns1+'CI_Contact']
        maintainerContactPhone = maintainerContact[ns1+'phone'][ns1+'CI_Telephone']
      
        record['maintainerphone'] = maintainerContactPhone[ns1+'voice'][ns2+'CharacterString'].text
        record['maintainerfax'] = maintainerContactPhone[ns1+'facsimile'][ns2+'CharacterString'].text

        maintainerContactAddress = maintainerContact[ns1+'address'][ns1+'CI_Address']
      
        record['maintaineraddress'] = maintainerContactAddress[ns1+'deliveryPoint'][ns2+'CharacterString'].text + '\n' + \
            maintainerContactAddress[ns1+'city'][ns2+'CharacterString'].text + '\n' + \
            maintainerContactAddress[ns1+'postalCode'][ns2+'CharacterString'].text + '\n' + \
            maintainerContactAddress[ns1+'country'][ns2+'CharacterString'].text
        record['maintaineremail'] = maintainerContactAddress[ns1+'electronicMailAddress'][ns2+'CharacterString'].text
      
        record['maintainerrole'] = decrypt_role(maintainer[ns1+'role'][ns1+'CI_RoleCode'].attrib['codeListValue'])
      
        record['datacatalogdate'] = root[ns1+'dateStamp'][ns2+'DateTime'].text
      
        details = None
        if root[ns1+'identificationInfo'].getchildren()[0].tag == (ns1+'MD_DataIdentification'):
            details = root[ns1+'identificationInfo'][ns1+'MD_DataIdentification']
        elif root[ns1+'identificationInfo'].getchildren()[0].tag == (ns3+'SV_ServiceIdentification'):
            details = root[ns1+'identificationInfo'][ns3+'SV_ServiceIdentification']
        #Rather bizarre case where the middle identifier is missing
        elif root[ns1+'identificationInfo'].getchildren()[0].tag == (ns1+'citation'):
            details = root[ns1+'identificationInfo']
        else:
            print 'Unknown entity type: ' + root[ns1+'identificationInfo'].getchildren()[0].tag + '. Quitting...'
            exit()
      
        detailsCitation = details[ns1+'citation'][ns1+'CI_Citation']
      
        record['title'] = detailsCitation[ns1+'title'][ns2+'CharacterString'].text
      
        record['datadate'] = ''
        if detailsCitation[ns1+'date'][ns1+'CI_Date'][ns1+'date'].getchildren()[0].tag == (ns2+'DateTime'):
            record['datadate'] = detailsCitation[ns1+'date'][ns1+'CI_Date'][ns1+'date'][ns2+'DateTime'].text
        elif detailsCitation[ns1+'date'][ns1+'CI_Date'][ns1+'date'].getchildren()[0].tag == (ns1+'extent'):
            record['datadate'] = detailsCitation[ns1+'date'][ns1+'CI_Date'][ns1+'date'][ns1+'extent'][ns4+'TimePeriod'][ns4+'beginPosition'].text + \
                ' - ' + detailsCitation[ns1+'date'][ns1+'CI_Date'][ns1+'date'][ns1+'extent'][ns4+'TimePeriod'][ns4+'endPosition'].text
        else:
            print 'Unknown citation date type: ' + detailsCitation[ns1+'date'].getchildren()[0].tag + '. Quitting...'
            exit()
      
        #Not worth doing lookup
        record['datadatetype'] = detailsCitation[ns1+'date'][ns1+'CI_Date'][ns1+'dateType']['CI_DateTypeCode'].attrib['codeListValue']
      
        record['url'] = detailsCitation[ns1+'identifier'][ns1+'MD_Identifier'][ns1+'code'][ns2+'CharacterString'].text

        #TODO: Consider doing lookup as above for role
        record['form'] = detailsCitation[ns1+'presentationForm'][ns1+'CI_PresentationFormCode'].attrib['codeListValue']

        record['abstract'] = details[ns1+'abstract'][ns2+'CharacterString'].text
      
        contact = details[ns1+'pointOfContact'][ns1+'CI_ResponsibleParty']
      
        #TODO, consider wrapping into function to handle this and maintainer above
        record['contactname'] = contact[ns1+'individualName'][ns2+'CharacterString'].text
        record['contactorganisation'] = contact[ns1+'organisationName'][ns2+'CharacterString'].text
        record['contactposition'] = contact[ns1+'positionName'][ns2+'CharacterString'].text
      
        contactDetails = contact[ns1+'contactInfo'][ns1+'CI_Contact']
        contactPhone = contactDetails[ns1+'phone'][ns1+'CI_Telephone']
        contactAddress = contactDetails[ns1+'address'][ns1+'CI_Address']
      
        record['contactphone'] = contactPhone[ns1+'voice'][ns2+'CharacterString'].text
        record['contactfax'] = contactPhone[ns1+'facsimile'][ns2+'CharacterString'].text
      
        record['contactaddress'] = contactAddress[ns1+'deliveryPoint'][ns2+'CharacterString'].text + '\n' + \
            contactAddress[ns1+'city'][ns2+'CharacterString'].text + '\n' + \
            contactAddress[ns1+'postalCode'][ns2+'CharacterString'].text + '\n' + \
            contactAddress[ns1+'country'][ns2+'CharacterString'].text
        record['contactemail'] = contactAddress[ns1+'electronicMailAddress'][ns2+'CharacterString'].text
      
        record['contactrole'] = decrypt_role(contact[ns1+'role'][ns1+'CI_RoleCode'].attrib['codeListValue'])

        #Not worth doing lookup
        record['frequpdated'] = details[ns1+'resourceMaintenance'][ns1+'MD_MaintenanceInformation'][ns1+'maintenanceAndUpdateFrequency'][ns1+'MD_MaintenanceFrequencyCode'].attrib['codeListValue']
        #....still inside details

        #Keywords. Nightmare. At the end we will go through and see how many unique categories of categories there are...
        keywordsXML = details[ns1+'descriptiveKeywords']

        record['keywords'] = dict()
      
        for keyworddata in keywordsXML:
            keywordstring = ''
            for keyword in keyworddata[ns1+'MD_Keywords'][ns1+'keyword']:
                keywordstring += '\"' + keyword[ns2+'CharacterString'].text + '\",'
            #Get rid of last commas
            keywordstring = keywordstring[0:len(keywordstring)-1]
            record['keywords'][keyworddata[ns1+'MD_Keywords'][ns1+'thesaurusName'][ns1+'CI_Citation'][ns1+'title'][ns2+'CharacterString'].text] = keywordstring
          
        #print record['keywords']
      
        #And just for extra merit, we have a topic category too for data entries
        record['topiccategory'] = ''
        try:
            topicCategory = details[ns1+'topicCategory'][ns1 + 'MD_TopicCategoryCode']
            record['topiccategory'] = details[ns1+'topicCategory'][ns1 + 'MD_TopicCategoryCode'].text
        except:
            pass
      
        record['uselimitations'] = details[ns1+'resourceConstraints'][0][ns1+'MD_Constraints'][ns1+'useLimitation'].text
        record['accesscontraints'] = ''
        record['useconstraints'] = ''
          
        if details[ns1+'resourceConstraints'][1][ns1+'MD_LegalConstraints'][ns1+'accessConstraints'][ns1+'MD_RestrictionCode'].attrib['codeListValue'] == 'restricted':
            record['accessconstraints'] = details[ns1+'resourceConstraints'][1][ns1+'MD_LegalConstraints'][ns1+'accessConstraints'][ns1+'MD_RestrictionCode'].text
        else:
            print 'WARNING: Didn\'t find a description of access restriction when expecting one'
        if details[ns1+'resourceConstraints'][1][ns1+'MD_LegalConstraints'][ns1+'useConstraints'][ns1+'MD_RestrictionCode'].attrib['codeListValue'] == 'license':
            record['useconstraints'] = details[ns1+'resourceConstraints'][1][ns1+'MD_LegalConstraints'][ns1+'useConstraints'][ns1+'MD_RestrictionCode'].text
        else:
            print 'WARNING: Didn\'t find a description of use license when expecting one'
          
        distributionInfo = root[ns1+'distributionInfo'][ns1+'MD_Distribution']
      
        record['format'] = distributionInfo[ns1+'distributionFormat'][ns1+'MD_Format'][ns1+'name'][ns2+'CharacterString'].text
        record['geo'] = ''
      
        if any(x.upper() in record['format'].upper() for x in geofiletypes):
            record['geo'] = 'x'
            print 'INFO: Geo data found. Format was ' + record['format']
        else:
            print 'INFO: Not geo. Format was ' + record['format']
          
          
        #TODO, consider wrapping into function to handle this and maintainer above
        distributionDetails = distributionInfo[ns1+'distributor'][ns1+'MD_Distributor']  
        distributorContact = distributionDetails[ns1+'distributorContact'][ns1+'CI_ResponsibleParty']
      
        record['distributorname'] = distributorContact[ns1+'individualName'][ns2+'CharacterString'].text
        record['distributororganisation'] = distributorContact[ns1+'organisationName'][ns2+'CharacterString'].text
        record['distributorposition'] = distributorContact[ns1+'positionName'][ns2+'CharacterString'].text
      
        distributorContactDetails = distributorContact[ns1+'contactInfo'][ns1+'CI_Contact']
        distributorContactPhone = distributorContactDetails[ns1+'phone'][ns1+'CI_Telephone']
        distributorContactAddress = distributorContactDetails[ns1+'address'][ns1+'CI_Address']
      
        record['distributorphone'] = distributorContactPhone[ns1+'voice'][ns2+'CharacterString'].text
        record['distributorfax'] = distributorContactPhone[ns1+'facsimile'][ns2+'CharacterString'].text
      
        record['distributoraddress'] = distributorContactAddress[ns1+'deliveryPoint'][ns2+'CharacterString'].text + '\n' + \
            distributorContactAddress[ns1+'city'][ns2+'CharacterString'].text + '\n' + \
            distributorContactAddress[ns1+'postalCode'][ns2+'CharacterString'].text + '\n' + \
            distributorContactAddress[ns1+'country'][ns2+'CharacterString'].text
        record['distributoremail'] = distributorContactAddress[ns1+'electronicMailAddress'][ns2+'CharacterString'].text
      
        record['distributorrole'] = decrypt_role(distributorContact[ns1+'role'][ns1+'CI_RoleCode'].attrib['codeListValue'])
      
        record['costs'] = distributionDetails[ns1+'distributionOrderProcess'][ns1+'MD_StandardOrderProcess'][ns1+'fees'][ns2+'CharacterString'].text
      
        #Not worth doing look up
        record['maintenanceInfo'] = root[ns1+'metadataMaintenance'][ns1+'MD_MaintenanceInformation'][ns1+'maintenanceAndUpdateFrequency'][ns1+'MD_MaintenanceFrequencyCode'].attrib['codeListValue']

        records.append(record)
        #Testing, one entry only
        #exit()
      
print 'Done parsing. ' +str(len(records)) + ' records found.'

#Find out how many categories of categories
categorizations = []

for record in records:
    for key in record['keywords'].keys():
        if key not in categorizations:
            categorizations.append(key)

print 'There are ' + str(len(categorizations)) + ' categorization schemes: \n' + str(categorizations)

#Read in files and licenses
fileslookup = {}
licenselookup = {}
with (open('../metadata/ulm/catalogfiles.csv', 'rb')) as csvinfile:
    datareader = csv.reader(csvinfile, delimiter=',')
    
    for row in datareader:
        if row[1] == 'file':
            if row[0] not in fileslookup:
                fileslookup[row[0]] = []
            fileslookup[row[0]].append(row[2])
        elif row[1] == 'license':
            if row[0] not in licenselookup:
                licenselookup[row[0]] = row[2]

allrecords = []
datafordb = []

for record in records:
    printsafeurl = metautils.findLcGermanCharsAndReplace(record['url'].lower())
    print 'Processing ' + printsafeurl
    row = metautils.getBlankRow()
    
    #Store the XML in the DB, but don't store it again in the JSON (which we will also store in the DB
    row['metadata_xml'] = record['xml']
    del record['xml']
    
    #Get license and files info from the HTML (stored during download of XML files)
    if record['url'] in licenselookup:
        row[u'Lizenz'] = licenselookup[record['url']]
        record['license'] = licenselookup[record['url']]
    else:
        row[u'Lizenz'] = ''
        record['license'] = []
        print 'WARNING: Couldn\'t find a license for ' + printsafeurl
        
    if record['url'] in fileslookup:
        row['files'] = fileslookup[record['url']]
        record['files'] = fileslookup[record['url']]
    else:
        row['files'] = []
        record['files'] = []
        print 'WARNING: Couldn\'t find any files for ' + printsafeurl
    
    row['metadata'] = record

    row[u'Stadt'] = 'ulm'
    row[u'Dateibezeichnung'] = record['title']
    row[u'Beschreibung'] = record['abstract']
    row[u'URL PARENT'] = record['url']
    row[u'Format'] = record['format']
    row[u'geo'] = record['geo']
    if record['costs'] is not None:
        row[u'Kosten'] = record['costs']  
    row[u'Zeitlicher Bezug'] = record['datadate'][0:4]

    groups = u''

    if ('GOV-Data Kategorien' in record and len(record['GOV-Data Kategorien']) > 0):
        for group in record['GOV-Data Kategorien']:
            odm_cats = metautils.govDataLongToODM(group)
            if len(odm_cats) > 0:
                for cat in odm_cats:
                    row[cat] = 'x'
                row[u'Noch nicht kategorisiert'] = ''
                
    allrecords.append(record)
    datafordb.append(row)
    
#Dump to file
with open('../metadata/ulm/catalog.json', 'wb') as outfile:
    json.dump(allrecords, outfile)

#Add to DB
metautils.setsettings(settings)
#Remove this catalog's data
metautils.removeDataFromPortal('daten.ulm.de')
#Add data
metautils.addDataToDB(datafordb=datafordb, originating_portal='daten.ulm.de', checked=True, accepted=True)


                    
                  



