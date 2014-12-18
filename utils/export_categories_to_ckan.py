# -*- coding: utf-8 -*-
import urllib2
import urllib
import json
import pprint

import metautils

url = ''
apikey = ''


def create_group(name):
    dataset_dict = {}
    dataset_dict['title'] = name
    dataset_dict['id'] = metautils.force_alphanumeric_short(name)
    dataset_dict['name'] = metautils.force_alphanumeric_short(name)
    data_string = urllib.quote(json.dumps(dataset_dict))
    request = urllib2.Request(url + '/api/3/action/group_create')
    request.add_header('Authorization', apikey)
    response = urllib2.urlopen(request, data_string)
    response_dict = json.loads(response.read())
    pprint.pprint(name + ": " + str(response_dict['success']))
    assert(response_dict['success'] == True)

map(create_group, metautils.getCategories())








