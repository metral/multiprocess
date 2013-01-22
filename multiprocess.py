#===============================================================================
#!/usr/bin/env python
#-------------------------------------------------------------------------------
import conf
from multiprocessing import Manager, Pool
from random import randint
from utils import Utils
import httplib
import json
import re
import sys
import time
import urllib

OS_USERNAME=str(sys.argv[1])
OS_PASSWORD=str(sys.argv[2])
OS_TENANT_NAME=str(sys.argv[3])
OS_TENANT_ID=str(sys.argv[4])

NOVA_API = conf.NOVA_API
CINDER_API = conf.CINDER_API
GLANCE_API = conf.GLANCE_API
KEYSTONE_API = conf.KEYSTONE_API
SWIFT_API = conf.SWIFT_API

os_processes = int(sys.argv[5])
iterations = int(sys.argv[6])

manager = Manager()

global_server_creating = manager.list([])
global_volume_creating = manager.list([])

global_server_created = manager.list([])
global_volume_created = manager.list([])

global_volume_attaching = manager.list([])
#-------------------------------------------------------------------------------
def millis():
    return int(round(time.time() * 1000))

#-------------------------------------------------------------------------------
# Get x-auth-token for user, password & tenant combo
def get_x_auth_token():
    params = '{"auth": {"passwordCredentials":{"username": "%s", ' \
            '"password": "%s"}, "tenantName": "%s"}}' \
            % (OS_USERNAME, OS_PASSWORD, OS_TENANT_NAME)

    headers = {"Content-Type": "application/json"}

    # HTTP connection
    conn = httplib.HTTPConnection(KEYSTONE_API)
    conn.request("POST", "/v2.0/tokens", params, headers)

    # HTTP response
    response = conn.getresponse()
    data = response.read()
    dd = json.loads(data)

    conn.close()
    apitoken = dd['access']['token']['id']

    return apitoken
#-------------------------------------------------------------------------------
def server_create_posts(post):
    # sleep to throttle create requests
    # this is to try to get around broken scheduler functionality in folsom
    time.sleep(randint(10,15))
    
    apitoken = get_x_auth_token()
    headers = {"x-auth-token": str(apitoken),
            "Content-Type": "application/json",
            }
    url, path, params = post
    conn = httplib.HTTPConnection(url)
    conn.request("POST", path, params, headers)
    res = conn.getresponse()

    json_data = json.loads(res.read())
    
    server_uuid = ""
    
    try:
        server_uuid = str(json_data['server']['id'])
    except:
        pass
    
    if server_uuid:
        global_server_creating.append(server_uuid)
#-------------------------------------------------------------------------------
def volume_create_posts(post):
    apitoken = get_x_auth_token()
    headers = {"x-auth-token": str(apitoken),
            "Content-Type": "application/json",
            }
    url, path, params = post
    conn = httplib.HTTPConnection(url)
    conn.request("POST", path, params, headers)
    res = conn.getresponse()

    json_data = json.loads(res.read())
    
    volume_uuid = ""
    
    try:
        volume_uuid = str(json_data['volume']['id'])
    except:
        pass
        
    if volume_uuid:
        global_volume_creating.append(volume_uuid)
#-------------------------------------------------------------------------------
def server_status_gets(get):
    while (True):
        server_status = ""
        server_uuid = ""
        
        apitoken = get_x_auth_token()
        headers = {"x-auth-token": str(apitoken)}
        
        url, path = get
        conn = httplib.HTTPConnection(url)
        conn.request("GET", path, "", headers)
        res = conn.getresponse()

        json_data = json.loads(res.read())

        try:
            server_status = \
                    str(json_data['server']['OS-EXT-STS:vm_state']).lower()
            server_uuid = \
                    str(json_data['server']['id']).lower()
        except:
            pass
            
        if (server_status == 'active'):
            global_server_created.append(server_uuid)
            print "Server Created: %s" % (server_uuid)
            break 
        else:
            time.sleep(2)
#-------------------------------------------------------------------------------
def volume_status_gets(get):
    while (True):
        volume_status = ""
        volume_uuid = ""
        
        apitoken = get_x_auth_token()
        headers = {"x-auth-token": str(apitoken)}
        
        url, path = get
        conn = httplib.HTTPConnection(url)
        conn.request("GET", path, "", headers)
        res = conn.getresponse()

        json_data = json.loads(res.read())

        try:
            volume_status = str(json_data['volume']['status']).lower()
            volume_uuid = str(json_data['volume']['id']).lower()
        except:
            pass
            
        if (volume_status == 'available'):
            global_volume_created.append(volume_uuid)
            print "Volume Created: %s" % (volume_uuid)
            break 
        elif (volume_status == 'in-use'):
            global_volume_created.append(volume_uuid)
            print "Volume Attached: %s" % (volume_uuid)
            break 
        else:
            time.sleep(2)
#-------------------------------------------------------------------------------
def volume_attach_posts(post):
    
    apitoken = get_x_auth_token()
    headers = {"x-auth-token": str(apitoken),
            "Content-Type": "application/json",
            }
    url, path, params = post
    conn = httplib.HTTPConnection(url)
    conn.request("POST", path, params, headers)
    res = conn.getresponse()
    
    json_data = json.loads(res.read())
    
    server_uuid = ""
    volume_uuid = ""
    
    try:
        server_uuid = str(json_data['volumeAttachment']['serverId'])
    except:
        pass
    
    try:
        volume_uuid = str(json_data['volumeAttachment']['volumeId'])
    except:
        pass
        
    if server_uuid and volume_uuid:
        global_volume_attaching.append(volume_uuid)
#-------------------------------------------------------------------------------
utils = Utils(OS_USERNAME, OS_PASSWORD, OS_TENANT_NAME, OS_TENANT_ID, NOVA_API,
        CINDER_API, GLANCE_API, KEYSTONE_API, SWIFT_API)

pool = Pool(processes = os_processes)
start_time = millis()

# Send requests to create servers & volumes
volume_create_conns = utils.volume_create_conns(iterations)
server_create_conns = utils.server_create_conns(iterations)
pool.map(volume_create_posts, volume_create_conns)
pool.map(server_create_posts, server_create_conns)

# Send requests to retrieve the status of the newly created servers & volumes
volume_status_conns = utils.volume_status_conns(iterations, global_volume_creating)
server_status_conns = utils.server_status_conns(iterations, global_server_creating)
if volume_status_conns: pool.map(volume_status_gets, volume_status_conns)
if server_status_conns: pool.map(server_status_gets, server_status_conns)

# Send requests to attach volumes to servers
volume_attach_conns = utils.volume_attach_conns(iterations, \
        global_server_created, global_volume_created)
if volume_attach_conns: pool.map(volume_attach_posts, volume_attach_conns)

# Send requests to retrieve the status of the newly attached volumes to servers
volume_status_conns = utils.volume_status_conns(iterations, global_volume_attaching)
if volume_status_conns: pool.map(volume_status_gets, volume_status_conns)

print "\nTotal took " + str(millis() - start_time) + " ms\n"
#-------------------------------------------------------------------------------
#===============================================================================
