import psycopg2.extras
import psycopg2
import urllib2
import urllib
import json
import pprint
import uuid

import metautils

from dbsettings import settings

metautils.setsettings(settings)

#This is a one time operation to create data based on the ODM DB
#Updates should be done using harvesters

url = ''
apikey = ''

dict_cur = metautils.getDBCursor(settings, dictCursor = True)
dict_cur.execute("SELECT * FROM data")

def category_to_group(groupname):
    # maybe some other id
    return {'name': metautils.force_alphanumeric_short(groupname)}

def openmap(open):
    if open is None:
        return 'Unbekannt'
    elif open:
        return 'Offen'
    else:
        return 'Nicht offen'

def dBtoCKAN(rec):
    d = {}
    d['owner_org'] = rec['city']
    d['state'] = 'active' if rec['accepted'] else 'deleted'
    d['url'] = rec['url']
    d['title'] = rec['title']
    d['name'] = str(uuid.uuid4()) #Must be unique, our titles are not
    if rec['description'] is not None:
        d['notes'] = rec['description']
    d['extras'] = []
    if rec['temporalextent'] is not None:
    d['extras'].append({'key': 'temporalextent', 'value': rec['temporalextent']})
    d['extras'].append({'key': 'metadata_source_type', 'value': metautils.convert_source_dict[rec['source']]})
    if rec['originating_portal'] is not None:
    d['extras'].append({'key': 'metadata_source_portal', 'value': rec['originating_portal']})
    if rec['metadata'] is not None:
    d['extras'].append({'key': 'original_metadata_json', 'value': rec['metadata']})
    if rec['metadata_xml'] is not None:
    d['extras'].append({'key': 'original_metadata_xml', 'value': rec['metadata_xml']})
    d['extras'].append({'key': 'openstatus', 'value': openmap(rec['open'])})
    if rec['licenseshort'] is not None:
    d['license_id'] = rec['licenseshort']
    if rec['open'] is not None:
    d['isopen'] = rec['open'] #Note that None gets mapped to False in CKAN
    if rec['publisher'] is not None:
    d['maintainer'] = rec['publisher']
    #N.B. groups have to be created, before they can be assigned
    #Groups are dictionaries. We use them via title which is what we store
    d['groups'] = map(category_to_group, rec['categories'])
    d['resources'] = set()
    #Duplicates in resources not allowed. Actually we shouldn't allow them either...
    rurls = set()
    for url in rec['filelist']:
        rurls.add(url)
    d['resources'] = []
    for url in rurls:
        d['resources'].append({'url': url})
    return d


def ckanCreate(url, apikey, rec):
    dataset_dict = dBtoCKAN(rec)
    data_string = urllib.quote(json.dumps(dataset_dict))
    request = urllib2.Request(url +'/api/action/package_create')
    request.add_header('Authorization', apikey)
    try:
        response = urllib2.urlopen(request, data_string)
    except:
        print 'ERROR Failed to create:'
        pprint.pprint(dataset_dict)
        raw_input("Press Enter to continue...")
    #response_dict = json.loads(response.read())
    #created_package = response_dict['result']
    #pprint.pprint(created_package)

for rec in dict_cur.fetchall():
    ckanCreate(url, apikey, rec)
