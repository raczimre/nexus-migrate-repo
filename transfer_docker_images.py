#!/usr/bin/python
from urllib import urlopen
from urlparse import urlparse
import json
import sys, os
import time

FAIL = '\033[91m'
OKBLUE = '\033[94m'

if len(sys.argv) != 3:
   print FAIL + 'Missing or incorrect number of runtime parameters!' + OKBLUE 
   print 'Usage: ' + str(sys.argv[0]) + ' <source docker registry url> <destination docker registry url>'
   print 'e.g.: ' + str(sys.argv[0]) + ' http://registry-docker-dev:5000 http://builder-docker-dev:5001'
   exit(1)
else:
   print 'Argument List:', str(sys.argv)
   print 'Starting to migrate images from ' + str(sys.argv[1]) + ' to ' + str(sys.argv[2]) + ' ...'

# src repo
src_docker_registry = urlparse(str(sys.argv[1]))

# dest repo
dest_docker_registry = urlparse(str(sys.argv[2]))

cat_url = src_docker_registry.geturl() + '/v2/_catalog?n=2000'
cat_response = urlopen(cat_url)
cat_item_dict = json.load(cat_response)
cat_item_count = len(cat_item_dict['repositories'])

start_time = time.time()

# iterate over the image list coming from the selected src repo
for i in range(cat_item_count):
    current_image_name = cat_item_dict['repositories'][i]

    tag_url = src_docker_registry.geturl() + '/v2/' + current_image_name + '/tags/list'
    tag_response = urlopen(tag_url)
    tag_item_dict = json.load(tag_response)
    tag_item_count = len(tag_item_dict['tags'])
    
    # iterate over the tags of the selected image in order to transfer all it's versions
    for j in range(tag_item_count):
        current_image_tag = tag_item_dict['tags'][j]
        current_image = current_image_name + ':' + current_image_tag
        print 'current image: ' + current_image

        os.system('docker pull ' + src_docker_registry.netloc + '/' + current_image)
        os.system('docker tag ' + src_docker_registry.netloc + '/' + current_image + ' ' + dest_docker_registry.netloc + '/' + current_image)
        os.system('docker push ' + dest_docker_registry.netloc + '/' + current_image)
    
    # iterate over the tags of the selected image again to remove all it's versions from the local image cache
    for j in range(tag_item_count):
        current_image_tag = tag_item_dict['tags'][j]
        print current_image_tag
        current_image = current_image_name + ':' + current_image_tag
        print 'current image: ' + current_image

        os.system('docker rmi -f ' + dest_docker_registry.netloc + '/' + current_image)
        os.system('docker rmi -f ' + src_docker_registry.netloc + '/' + current_image)

elapsed_time = time.time() - start_time
print 'elapsed _time: ' + str(elapsed_time)
