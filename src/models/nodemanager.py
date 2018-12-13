from cluster import CLUSTER
from config import DEF_PATHS, TIMEOUT, PORT
from utils import get_disk_usage, get_local_ip

import os
import requests

class NodeManager():

    def __init__(self):
        self.ip = get_local_ip()

    def init(self):
        access_ok = {}
        for path in DEF_PATHS:
            access_ok[path] = os.path.isdir(DEF_PATHS[path]) and os.access(DEF_PATHS[path], os.R_OK|os.W_OK)
        free = self.get_free_space()
        return access_ok, free

    def get_free_space(self):
        # todo: space in blocks, not bytes
        total, used, free = get_disk_usage('/mnt/sda1')
        return free

    def scan(self, root=DEF_PATHS['INCOMING']):
        resl = []
        root = os.path.abspath(root)
        if os.path.isdir(root):
            if not(root.endswith(os.sep)):
                root = root + os.sep
            for dirpath, dirnames, filenames in os.walk(root):
                for filepath in filenames:
                    resl.append(os.path.join(dirpath, filepath))
        else:
            resl.append(root)
        return resl

    def call_peers(self, timeout=TIMEOUT):
        resl = []
        for ip in CLUSTER:
            if (ip != self.ip):
                api_url = 'http://' + ip + ':' + str(PORT) + '/status'
                res = requests.get(api_url)
                if(200 == res.status_code):
                    resl.append(res.text)
        return resl
