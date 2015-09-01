# -*- coding: utf-8 -*-
import urllib, urllib2, json
import unicodecsv as csv
import sys
import os
import ckanapi
import traceback

#This script migrates data that was thought not to have been and will not be harvested
url = "https://offenedaten.de"
#For beta (write access)
uploadurl="http://beta.offenedaten.de"
apikey=os.environ['CKANAPIKEY']

mysite = ckanapi.RemoteCKAN(uploadurl, apikey=apikey, user_agent='okfdemigrate/1.0 (+http://beta.offenedaten.de)')

if len(sys.argv) > 1:
    print 'Loading from file...'
    jsonurl = open(sys.argv[1], 'rb')
    groups = json.loads(jsonurl.read())
    jsonurl.close()
    
if len(sys.argv) < 2:
    jsonurl = urllib.urlopen(url + "/api/3/action/package_list")
    listpackages = json.loads(jsonurl.read())
    listpackages = listpackages['result']
    groups = []
    if len(sys.argv) < 2:
        for item in listpackages:
            urltoread = url + "/api/3/action/package_show?id=" + item
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
    with open('odcatalog.json', 'wb') as outfile:
        json.dump(groups, outfile)

#n.b. owner_org in 2.2 is id, in 2.3 it is name, and name is probably fine for adding anyway
for package in groups:
    print 'Examining ' + package['name']
    #This list is exhaustive at time of writing
    #Original run was done without 'name' key and didn't work. Not tested.
    if not ('organization' in package and package['organization']['name'] in ("okf-de", "codingdavinci", "ubleipzig")):
        print 'Package has no useful organization, looking at the ' + str(len(package['groups'])) + ' groups'
        if len(package['groups'])>0:
            if package['groups'][0]['name'] == "mogdy":
                package['owner_org'] = "mogdy"
            elif package['groups'][0]['name'] == "quellensammlung-mpiwg":
                package['owner_org'] = "mpiwg"
            elif package['groups'][0]['name'] == "sonderfreigaben":
                package['owner_org'] = "apps4deutschland"
            elif package['groups'][0]['name'] == "stadt-mittenwalde":
                package['owner_org'] = "mittenwalde"
            elif package['groups'][0]['name'] == "stadt-paderborn":
                package['owner_org'] = "paderborn"
            else:
                print 'Package has no matching group (' + package['groups'][0]['name'] +'). Not adding.'
                continue #Without adding
        else:
            #Package has no org-like categorization. Probably an upload of something that should be kept.
            #BUT should have checked for things harvested from govdata (see remove script)
            package['owner_org'] = "okf-de"
            print 'Package had no organization and no groups. Assigned to OKFDE'
            
    #If we got this far we have something we want to add
    package['groups'] = [{'name': 'noch-nicht-kategorisiert'},] #'Reset' groups

    print 'Creating the package, without resources'
    
    data_string = urllib.quote(json.dumps(package))
    request = urllib2.Request(uploadurl +'/api/action/package_create')
    request.add_header('Authorization', apikey)
    try:
        response = urllib2.urlopen(request, data_string)
    except:
        print 'ERROR Failed to create: ' + package['name']
        print traceback.format_exc()
        raw_input("Press Enter to continue...")

    print 'Added package'
    
    resources = []
    if ('resources' in package):
        resources = package['resources']
        del package['resources']

    for file in resources:
        file['package_id'] = package['id']
        del file['tracking_summary']
        try:
            if (file['url'] not in [None, '']) and ('offenedaten.de' in file['url']):
                #download file!
                target = file['url'].split('/')[-1]
                urllib.urlretrieve (file['url'], target);
                print 'Downloaded ' + target
                mysite.call_action('resource_create', file, files={'upload': open(target)})
                print 'Added resource WITH upload'
            else:
                mysite.call_action('resource_create', file)
                print 'Added resource WITHOUT upload'
        except:
            print traceback.format_exc()
            raw_input("Press Enter to continue...")

