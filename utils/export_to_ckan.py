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


def dBtoCKAN(rec):
    d = {}
    d['owner_org'] = rec['originating_portal']
    d['state'] = 'active' if rec['accepted'] else 'deleted'
    d['url'] = rec['url']
    d['title'] = rec['title']
    d['name'] = str(uuid.uuid4()) #Must be unique, our titles are not
    d['notes'] = rec['description']
    d['extras'] = []
    d['extras'].append({'key': 'temporalextent', 'value': rec['temporalextent']})
    d['extras'].append({'key': 'location', 'value': rec['city']})
    d['extras'].append({'key': 'source', 'value': rec['source']})
    d['extras'].append({'key': 'original_metadata_json', 'value': rec['metadata']})
    d['extras'].append({'key': 'original_metadata_xml', 'value': rec['metadata_xml']})
    d['license_id'] = rec['licenseshort']
    d['isopen'] = rec['open']
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
        print 'ERROR: \n' + dataset_dict['title'] + ', ' + dataset_dict['url']
        return
    response_dict = json.loads(response.read())
    #created_package = response_dict['result']
    #pprint.pprint(created_package)


for rec in dict_cur.fetchall():
    ckanCreate(url, apikey, rec)

