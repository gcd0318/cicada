from cluster import CLUSTER
from config import DEF_PATHS, TIMEOUT, PORT
from utils import get_disk_usage, get_local_ip, get_path_size

from rediscluster import StrictRedisCluster

import glob
import json
import os
import requests


class NodeDAO(StrictRedisCluster):
    def __init__(self, host='127.0.0.1', port='7001'):
        startup_nodes = [{"host": host, "port": port}]
        StrictRedisCluster.__init__(self, startup_nodes=startup_nodes, decode_responses=True)


class NodeManager():
    def __init__(self):
        self.ip = get_local_ip()
        self.dao = NodeDAO()
        self.set_accesses()
        self.set_free_space()
        print(self.ip)

    def are_accessible(self):
        access_ok = {}
        for path in DEF_PATHS:
            access_ok[path] = os.path.isdir(DEF_PATHS[path]) and os.access(DEF_PATHS[path], os.R_OK|os.W_OK)
        return access_ok

    def free_space(self):
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

    def write_to_db(self, k, v):
        res = self.dao.get(self.ip)
        if res is None:
            self.dao.set(self.ip, json.dumps({k: v}))
        else:
            resd = json.loads(res)
            resd[k] = v
            self.dao.set(self.ip, json.dumps(resd))

    def read_from_db(self, k):
        res = None
        params = json.loads(self.dao.get(self.ip))
        if params is not None:
            res = params.get(k)
        return res

    def set_free_space(self):
        return self.write_to_db('free', self.free_space())

    def get_free_space(self):
        return self.read_from_db('free')

    def set_accesses(self):
        return self.write_to_db('accesses', self.are_accessible())
    def get_accesses(self):
        return self.read_from_db('accesses')

    def set_status(self, status):
        return self.write_to_db('status', status)

    def get_status(self):
        return self.read_from_db('status')

    def refresh_incoming(self):
        paths = {}
        for p in glob.glob(DEF_PATHS['INCOMING'] + '*'):
            if os.path.isdir(p):
                p = p + os.sep
            paths[p] = get_path_size(p)
        return paths
