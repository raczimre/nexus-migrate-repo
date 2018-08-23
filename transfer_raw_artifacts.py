#!/usr/bin/python
from urllib import urlopen
import json
import sys, os
import time
from urlparse import urlparse
import getpass

FAIL = '\033[91m'
OKBLUE = '\033[94m'

if len(sys.argv) != 4:
   print FAIL + 'Missing or incorrect number of runtime parameters!' + OKBLUE
   print 'Usage: ' + str(sys.argv[0]) + ' <source repo url> <destination repo url> <repo name>'
   print 'e.g.: ' + str(sys.argv[0]) + ' http://alm-docker-dev:8081 http://builder-docker-dev:8081 docker-dependencies'
   exit(1)
else:
   print 'Argument List:', str(sys.argv)
   print 'Starting to migrate ' + str(sys.argv[3]) + ' from ' + str(sys.argv[1]) + ' to ' + str(sys.argv[2]) + ' ...'

user = raw_input("Username:")
passwd = getpass.getpass("Password for " + user + ":")

# src repo
src_raw_repo = urlparse(str(sys.argv[1]))

# dest repo
dest_raw_repo = urlparse(str(sys.argv[2]))

repo_name = str(sys.argv[3])

cat_url = src_raw_repo.geturl() + '/service/rest/v1/components?repository=' + repo_name
cat_response = urlopen(cat_url)
cat_item_dict = json.load(cat_response)
cat_item_count = len(cat_item_dict['items'])
continuation_token = cat_item_dict['continuationToken']

start_time = time.time()

# iterate over the artifact list coming from the selected src repo
while True:
  for i in range(cat_item_count):
    current_item = cat_item_dict['items'][i]
    current_asset = current_item['assets'][0]
    current_download_url = current_asset['downloadUrl']
    current_file_name = current_download_url.rpartition('/')[2]

    print 'download url: ' + current_download_url
    os.system('curl ' + current_download_url + ' -O -H "accept: application/json"')
	
    parsed_url = urlparse(current_download_url)
    upload_url = parsed_url._replace(netloc=dest_raw_repo.netloc).geturl()

    print 'upload url: ' + upload_url
    os.system('curl -v --insecure --user "' + user + ':' + passwd + '" --upload-file ./' + current_file_name + ' -L ' + upload_url)
    os.system('rm -f ' + current_file_name)

  if (continuation_token == "string" or continuation_token == "" or not continuation_token):
    break
  else:
    print 'continuation token: ' + continuation_token
    cat_url = src_raw_repo.geturl() + '/service/rest/v1/components?continuationToken=' + continuation_token + '&repository=' + repo_name
    cat_response = urlopen(cat_url)

    cat_item_dict = json.load(cat_response)
    cat_item_count = len(cat_item_dict['items'])
    continuation_token = cat_item_dict['continuationToken']

elapsed_time = time.time() - start_time
print 'elapsed _time: ' + str(elapsed_time)

