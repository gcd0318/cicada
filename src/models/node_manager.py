from gcutils.fileops import get_disk_usage, get_path_size
from gcutils.netops import get_local_ip
try:
    from rediscluster import StrictRedisCluster
except:
    from rediscluster import StrictRedis as StrictRedisCluster

import json
import os
import requests

from const import TIMEOUT_s

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

    def insert_or_update_list(self, name, val):
        self.rpush(name, val)


class NodeDB():
    def __init__(self, username, password, host='127.0.0.1', port=5678, client_encoding="UTF-8", dbname='cicada', dbtype='postgresql'):
        def _connect_postgresql(dbname, username, password, host, port=5678, client_encoding=client_encoding):
            import psycopg2
            return psycopg2.connect(dbname=dbname, user=username, password=password, port=port, host=host, client_encoding=client_encoding)
        def _connect_mysql(dbname, username, password, host, port=5678, client_encoding=client_encoding):
            import mysql.connector
            from mysql.connector import connection
            return connection.MySQLConnection(dbname=dbname, user=username, password=password, port=port, host=host, client_encoding=client_encoding)

        self.dbtype = dbtype
        self.conn = None
        if ('postgresql' == self.dbtype):
            self.conn = _connect_postgresql(dbname, username, password, host, port, client_encoding)
        elif(self.dbtype in ('mysql', 'mariadb')):
            self.conn = _connect_mysql(dbname, username, password, host, port, client_encoding)

#    def insert_or



class NodeManager():
    def __init__(self, conf, http_port=9999):
        self.ip = get_local_ip()
        self.redis = NodeRedis(self.ip)
        self.set_accesses()
        self.set_free_space()
        nodes = conf['cluster']['nodes']
        i = 0
        while (i < len(nodes)) and (cluster[nodes[i]] != self.ip):
            i = i + 1
        if i < len(nodes):
            node = nodes[i]
            self.incoming = node['incoming']
            self.backup = node['backup']


    def are_accessible(self):
        access_ok = {}
        access_ok['INCOMING'] = os.path.isdir(self.incoming) and os.access(INCOMING, os.R_OK | os.W_OK)
        access_ok['BACKUP'] = os.path.isdir(self.backup) and os.access(BACKUP, os.R_OK | os.W_OK)
        return access_ok

    def free_space(self):
        # todo: space in blocks, not bytes
        _, _, incoming_free = get_disk_usage(self.incoming)
        _, _, backup_free = get_disk_usage(self.backup)
        return {'INCOMING': incoming_free, 'BACKUP': backup_free}

    def call_peers(self, timeout=TIMEOUT_s):
        resl = []
        for ip in CLUSTER:
            if (ip != self.ip):
                api_url = 'http://' + ip + ':' + str(http_port) + '/status'
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
        return self.read_from_redis_str(k) == v

    def read_redis_str(self, k):
        res = self.redis.get(k)
        if res is not None:
            res = json.loads(res)
        return res

    def read_redis_dict(self, k, field=None):
        res = None
        if field is not None:
            res = self.redis.hmget(k, field)
        return res

    def read_from_redis_str(self, k=None):
        res = None
        params = self.read_redis_str(self.ip)
        if k is None:
            res = params
        else:
            if params is not None:
                res = params.get(k)
        return res

    def read_from_redis_dict(self, k=None, fields=None):
        res = None
        if k is not None and fields is not None:
            res = self.read_redis_dict(k, fields)
        return res

    def set_free_space(self):
        return self.write_to_redis('free', self.free_space())

    def get_free_space(self):
        return self.read_from_redis_str('free')

    def set_accesses(self):
        return self.write_to_redis('accesses', self.are_accessible())
    def get_accesses(self):
        return self.read_from_redis_str('accesses')

    def set_status(self, status):
        return self.write_to_redis('status', status)

    def get_status(self):
        return self.read_from_redis_str('status')
