#!/usr/bin/python3
from __future__ import print_function

from html.parser import HTMLParser
import json
import logging
import os
import re
import requests
import time
import html

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.ERROR)

session = requests.Session()

username = os.environ['COMCAST_USERNAME']
password = os.environ['COMCAST_PASSWORD']

logger.debug("Finding form inputs for login...")
res = session.get('https://customer.xfinity.com/oauth/force_connect/?continue=%23%2Fdevices')
#res = session.get('https://login.comcast.net/login?r=comcast.net&s=oauth&continue=https%3A%2F%2Flogin.comcast.net%2Foauth%2Fauthorize%3Fclient_id%3Dmy-account-web%26redirect_uri%3Dhttps%253A%252F%252Fcustomer.xfinity.com%252Foauth%252Fcallback%26response_type%3Dcode%26state%3D%2523%252Fdevices%26response%3D1&client_id=my-account-web')
assert res.status_code == 200
data = {x[1]: html.unescape(x[2]) for x in re.finditer(r'<input.*?name="(.*?)".*?value="(.*?)".*?>', res.text)}
logger.debug("Found with the following input fields: {}".format(data))
data = {
    'user': username,
    'passwd': password,
    **data
}

logger.debug("Posting to login...")
res = session.post('https://login.xfinity.com/login', data=data)
# clone of logic from https://github.com/BrendanGrant/ComcastUsageChecker/blob/master/ComcastUsageChecker/Program.cs#L94 Dont_Follow_Redirects_And_Craft_Broken_Url_To_Get_Usage() method
# turns out not to be needed? to enable this also add , allow_redirects=True to the above request
# if res.status_code == 302:
#     # For reasons unknown, the server replies with an incomplete URL, but what is needed is easy enough to detect and add... though ugly.
#     locationUrl = str(res.headers['Location'])
#     if (locationUrl.find("client_id") == -1):
#         newQuery = "client_id=my-account-web&prompt=login&redirect_uri=https%3A%2F%2Fcustomer.xfinity.com%2Foauth%2Fcallback&response_type=code&state=%23%2Fdevices&response=1"
#         newUri = locationUrl + "?" + newQuery
#         res = session.get(newUri)
assert res.status_code == 200

logger.debug("Fetching internet usage AJAX...")
res = session.get('https://customer.xfinity.com/apis/services/internet/usage')
#logger.debug("Resp: %r", res.text)
assert res.status_code == 200

js = json.loads(res.text)

out = {
    'raw': js,
    'used': js['usageMonths'][-1]['homeUsage'],
    'total': js['usageMonths'][-1]['allowableUsage'],
    'unit': js['usageMonths'][-1]['unitOfMeasure'],
}
print(json.dumps(out))
