# -*- coding: utf-8 -*-
import urllib, urllib2, json
import sys
import os
import traceback

#This script removes data that shouldn't have been added
url="http://beta.offenedaten.de"
apikey=os.environ['CKANAPIKEY']

if len(sys.argv) > 1:
    print 'Loading from file...'
    jsonurl = open(sys.argv[1], 'rb')
    groups = json.loads(jsonurl.read())
    jsonurl.close()
    
if len(sys.argv) < 2:
    jsonurl = urllib.urlopen(url + "/api/3/action/organization_show?id=okf-de&include_datasets=true")
    listpackages = json.loads(jsonurl.read())
    listpackages = listpackages['result']['packages']
    groups = []
    for item in listpackages:
        urltoread = url + "/api/3/action/package_show?id=" + item['name']
        print 'Downloading ' + urltoread
        trycount = 0
        try:
            req = urllib2.Request(urltoread.encode('utf8'))
            resp = urllib2.urlopen(req)
            urldata = resp.read()
        except IOError:
            if trycount == 100:
                print 'Download failed 100 times, giving up...'
                exit()
            print 'Something went wrong, retrying...'
            trycount += 1
        pdata = json.loads(urldata)
        if 'success' in pdata and pdata['success']:
            groups.append(pdata['result'])

if len(sys.argv) < 2:
    with open('odcatalogsuspect.json', 'wb') as outfile:
        json.dump(groups, outfile)

for package in groups:
    print 'Examining ' + package['name']

    for item in package['extras']:
        if item['key'] == 'harvest_url':
            print 'harvest url: ' + item['value']
            if 'govdata' in item['value']:
                print 'REMOVING'
                print url +'/api/action/package_delete?id='+package['id']
                request = urllib2.Request(url +'/api/action/package_delete')
                request.add_header('Authorization', apikey)
                try:
                    response = urllib2.urlopen(request, json.dumps({'id': package['id']}))
                except:
                    print 'ERROR Failed to delete: ' + package['name']
                    print traceback.format_exc()
                    raw_input("Press Enter to continue...")
            else: print 'NOT REMOVING'
                