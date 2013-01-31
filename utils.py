#===============================================================================
#!/usr/bin/env python
#-------------------------------------------------------------------------------
import sys
import json
from time import time
import random
#-------------------------------------------------------------------------------
class Utils:
    OS_USERNAME = ""
    OS_PASSWORD = ""
    OS_TENANT_NAME = ""
    OS_TENANT_ID = ""
    
    NOVA_API = ""
    CINDER_API = ""
    GLANCE_API = ""
    KEYSTONE_API = ""
    SWIFT_API = ""
    
    FLAVOR_ID = ""
    IMAGE_ID = ""
    KEYPAIR_NAME = ""
#-------------------------------------------------------------------------------
    def __init__(self, OS_USERNAME, OS_PASSWORD, OS_TENANT_NAME, OS_TENANT_ID,
            NOVA_API, CINDER_API, GLANCE_API, KEYSTONE_API, SWIFT_API,
            FLAVOR_ID, IMAGE_ID, KEYPAIR_NAME):
        self.OS_USERNAME=OS_USERNAME
        self.OS_PASSWORD=OS_PASSWORD
        self.OS_TENANT_NAME=OS_TENANT_NAME
        self.OS_TENANT_ID=OS_TENANT_ID

        self.NOVA_API=NOVA_API
        self.CINDER_API=CINDER_API
        self.GLANCE_API=GLANCE_API
        self.KEYSTONE_API=KEYSTONE_API
        self.SWIFT_API=SWIFT_API
        
        self.FLAVOR_ID = FLAVOR_ID
        self.IMAGE_ID = IMAGE_ID
        self.KEYPAIR_NAME = KEYPAIR_NAME
#-------------------------------------------------------------------------------
    def b64_encode(self, filepath):
        b64 = ""

        with open(filepath, "rb") as f:
            data = f.read()
            b64 = data.encode("base64")
            
        return b64
#-------------------------------------------------------------------------------
    def randomNumber(self):
        return str(int(time())) + "-" + str(random.randint(10000000,99999999))
#-------------------------------------------------------------------------------
    def server_create_conns(self, iterations):
        connections = []

        for i in range(0, iterations):
            url = self.NOVA_API
            path = "/".join(["/v2", self.OS_TENANT_ID, "servers"])

            path_1 = "/root/vg_test.sh"
            b64_1 = self.b64_encode("vm_scripts/vg_test.sh")

            path_2 = "/etc/rc.local"
            b64_2 = self.b64_encode("vm_scripts/rc.local")

            post_params = { 
                    "server": {
                        "flavorRef": self.FLAVOR_ID,
                        "imageRef": self.IMAGE_ID,
                        "name": "foobar-server-" + self.randomNumber(),
                        "key_name": self.KEYPAIR_NAME,
                        "personality": [
                            {
                                "contents": b64_1,
                                "path": path_1
                                },
                            {
                                "contents": b64_2,
                                "path": path_2
                                }
                            ]
                        }
                    }
            params = json.dumps(post_params)
            connections.append((url, path, params))

        return connections
#-------------------------------------------------------------------------------
    def volume_create_conns(self, iterations):
        connections = []

        for i in range(0, iterations):
            url = self.CINDER_API
            path = "/".join(["/v1", self.OS_TENANT_ID, "volumes"])
            
            post_params = { 
                    "volume": {
                        "size": 1,
                        "display_name": "foobar-volume-" + self.randomNumber(),
                        }
                    }
            params = json.dumps(post_params)
            connections.append((url, path, params))

        return connections
#-------------------------------------------------------------------------------
    def server_status_conns(self, servers):
        connections = []

        for server_uuid in servers:
            url = self.NOVA_API
            path = "/".join(["/v2", self.OS_TENANT_ID, "servers", server_uuid])
            connections.append((url, path))

        return connections
#-------------------------------------------------------------------------------
    def volume_status_conns(self, volumes):
        connections = []
        
        for volume_uuid in volumes:
            url = self.CINDER_API
            path = "/".join(["/v1", self.OS_TENANT_ID, "volumes", volume_uuid])
            connections.append((url, path))

        return connections
#-------------------------------------------------------------------------------
    def volume_attach_conns(self, iterations, servers_created, volumes_created):
        connections = []
        
        for i in range(0, iterations):
            try:
                server_uuid = servers_created[i]
            except:
                server_uuid = None
                pass
            
            try:
                volume_uuid = volumes_created[i]
            except:
                volume_uuid = None
                pass

            if server_uuid and volume_uuid:
                url = self.NOVA_API
                path = "/".join(["/v2", self.OS_TENANT_ID, "servers", \
                        server_uuid, "os-volume_attachments"])

                post_params = { 
                        "volumeAttachment": {
                            "volumeId": volume_uuid,
                            "device": "/dev/vdc"
                            }
                        }

                params = json.dumps(post_params)
                connections.append((url, path, params))

        return connections
#-------------------------------------------------------------------------------
#===============================================================================
