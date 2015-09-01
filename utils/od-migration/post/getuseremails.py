# -*- coding: utf-8 -*-
import urllib, urllib2, json
import os

#This script removes data that shouldn't have been added
url="https://offenedaten.de"
apikey=os.environ['CKANAPIKEY']

request = urllib2.Request(url +'/api/3/action/user_list')
request.add_header('Authorization', apikey)
response = urllib2.urlopen(request, "")
response_dict = json.loads(response.read())

listpackages = response_dict['result']
for item in listpackages:
    print item['email']