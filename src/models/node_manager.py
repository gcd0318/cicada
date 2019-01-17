from config import CLUSTER, TIMEOUT, HTTP_PORT, INCOMING, BACKUP
from utils import get_disk_usage, get_local_ip, get_path_size
from rediscluster import StrictRedisCluster

import json
import os
import requests

class NodeRedis(StrictRedisCluster):
    def __init__(self, host='127.0.0.1', port='7001'):
        startup_nodes = [{"host": host, "port": port}]
        StrictRedisCluster.__init__(self, startup_nodes=startup_nodes, decode_responses=True)

    def insert_or_update_str(self, name, val):
        self.set(name, val)
#    def get(self, name):
#        return self.get(name)

    def insert_or_update_dict(self, name, dic):
        if self.exists(name):
            print(self.hgetall(name))
            for k in dic:
                self.hset(name, k, dic[k])
        else:
            self.hmset(name, dic)
        res = True
        for k in dic:
            res = res and self.hget(name, k) == dic[k]
        return res

    def insert_or_update_set(self, name, *vals):
        self.sadd(name, *vals)
        res = True
        s_tmp = self.smembers(name)
        for val in vals:
            res = res and (val in s_tmp)
        return res


class NodeManager():
    def __init__(self):
        self.ip = get_local_ip()
        self.redis = NodeRedis()
        self.set_accesses()
        self.set_free_space()

    def are_accessible(self):
        access_ok = {}
        access_ok['INCOMING'] = os.path.isdir(INCOMING) and os.access(INCOMING, os.R_OK | os.W_OK)
        access_ok['BACKUP'] = os.path.isdir(BACKUP) and os.access(BACKUP, os.R_OK | os.W_OK)
        return access_ok

    def free_space(self):
        # todo: space in blocks, not bytes
        _, _, incoming_free = get_disk_usage(INCOMING)
        _, _, backup_free = get_disk_usage(BACKUP)
        return {'INCOMING': incoming_free, 'BACKUP': backup_free}

    def call_peers(self, timeout=TIMEOUT):
        resl = []
        for ip in CLUSTER:
            if (ip != self.ip):
                api_url = 'http://' + ip + ':' + str(HTTP_PORT) + '/status'
                res = requests.get(api_url)
                if(200 == res.status_code):
                    resl.append(res.text)
        return resl

    def write_redis(self, k, v):
        pass

    def write_to_redis(self, k, v):
        res = self.redis.get(self.ip)
        if res is None:
            self.redis.set(self.ip, json.dumps({k: v}))
        else:
            resd = json.loads(res)
            resd[k] = v
            self.redis.set(self.ip, json.dumps(resd))
        return self.read_from_redis(k) == v

    def read_redis(self, k):
        res = self.redis.get(k)
        if res is not None:
            res = json.loads(res)
        return res

    def read_from_redis(self, k=None):
        res = None
        params = self.read_redis(self.ip)
        if k is None:
            res = params
        else:
            if params is not None:
                res = params.get(k)
        return res

    def set_free_space(self):
        return self.write_to_redis('free', self.free_space())

    def get_free_space(self):
        return self.read_from_redis('free')

    def set_accesses(self):
        return self.write_to_redis('accesses', self.are_accessible())
    def get_accesses(self):
        return self.read_from_redis('accesses')

    def set_status(self, status):
        return self.write_to_redis('status', status)

    def get_status(self):
        return self.read_from_redis('status')
