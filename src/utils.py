from config import DNS, DEF_PATHS, PERIOD_s
from const import UTF8
from model import logger

from hashlib import md5

import paramiko

import glob
import os
import stat
import socket
import time


def get_func(f):
    def _wrapper(*argc, **kwargs):
        print('======================== running', f.__name__, '========================')
        logger.info('running ' + f.__name__)
        while True:
            try:
                f(*argc, **kwargs)
            except Exception as err:
                import traceback
                logger.error(f.__name__ + ': ' + str(err))
                logger.error(traceback.format_exc())
            time.sleep(PERIOD_s)
    return _wrapper

def deep_scan(root=DEF_PATHS['INCOMING']):
    resl = []
    root = os.path.abspath(root)
    if os.path.isdir(root):
        if not(root.endswith(os.sep)):
            root = root + os.sep
        for dirpath, dirnames, filenames in os.walk(root):
            if ([] == filenames):
                filenames.append('')
            for filepath in filenames:
                resl.append(os.path.join(dirpath, filepath))
    else:
        resl.append(root)
    return resl

def deep_scan_remote(sftp, path):
    res = []
    if (not path.endswith(os.sep)):
        path = path + os.sep
    for fobj in sftp.listdir_attr(path):
        filepath = path + fobj.filename
        if stat.S_ISDIR(fobj.st_mode):
            res = res + deep_scan_remote(sftp, filepath)
        else:
            res.append(filepath)
        if ([] == res):
            res = [path]
        return res

def scan(root=DEF_PATHS['INCOMING']):
    resl = []
    root = os.path.abspath(root)
    if os.path.isdir(root):
        if not(root.endswith(os.sep)):
            root = root + os.sep
        for filepath in glob.glob(root + '*'):
            if os.path.isdir(filepath):
                if not (filepath.endswith(os.sep)):
                    filepath = filepath + os.sep
            resl.append(filepath)
    else:
        resl.append(root)
    return resl

def get_local_ip(port=80):
    ip = None
    i = 0
    while (ip is None) and (i < len(DNS)):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((DNS[i], port))
            ip = s.getsockname()[0]
        except Exception as err:
            import traceback
            logger.error(str(err))
            logger.error(traceback.format_exc())
        finally:
            i = i + 1
            s.close()
    return ip

def get_local_hostname():
    return socket.gethostname() or None

def get_disk_usage(path='/'):
    st = os.statvfs(path)
    free = (st.f_bavail * st.f_frsize)
    total = (st.f_blocks * st.f_frsize)
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    return total, used, free

def get_path_size(path):
# todo: why 1024?
    import math

    size = 0
    if(os.path.isdir(path)):
        for root, dirs, files in os.walk(path):
            size = size + sum([math.ceil(os.path.getsize(os.path.join(root, name)) / 1024) * 1024 for name in files])
    elif(os.path.isfile(path)):
        size = math.ceil(os.path.getsize(path) / 1024) * 1024
    return size

def get_md5(filepath):
    res = None
    absfp = os.path.abspath(filepath)
    if os.path.isfile(absfp):
        m = md5()
        with open(absfp, 'rb') as f:
            b = f.read(8096)
            while(b):
                m.update(b)
                b = f.read(8096)
            res = m.hexdigest()
    elif os.path.isdir(absfp):
        pathmd5 = md5()
        pathmd5.update(absfp.encode(UTF8))
        path_md5 = pathmd5.hexdigest()
        with open(path_md5, 'w') as tmpf:
            for filename in deep_scan(absfp):
                print(get_md5(filename), file=tmpf)
        res = get_md5(path_md5)
        os.remove(path_md5)
    return res


def cp(src, tgt):
    res = ''
    if ('@' in src) or ('@' in tgt):
        res = remote_cp(src, tgt)
    else:
        res = ''
    return res

def remote_cp(src, tgt):
    # username:password@ip:port@path
    (local, remote) = (src, tgt) if ('@' in tgt) else (tgt, src)
    auth, sock, remote_path = remote.split('@')
    username, password = auth.split(':')
    if not(':' in sock):
        sock = sock + ':22'
    t = paramiko.Transport(sock)
    t.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(t)
    try:
        logger.debug('copy from ' + src + ' to ' + tgt)
        local = os.path.abspath(local)
        logger.debug('local file is as ' + local)
        if (local == src):
            if os.path.isdir(src):
                filename = src.split(os.sep)[-1]
                if not(remote_path.endswith(filename)):
                    if(not remote_path.endswith(os.sep)):
                        remote_path = remote_path + os.sep
                    remote_path = remote_path + filename
                sftp.put(src, remote_path)
            else:
                if (not remote_path.endswith(os.sep)):
                    remote_path = remote_path + os.sep
                for fullpath in deep_scan(src):
                    fplist = fullpath.replace(src).split(os.sep)
                    rel_path = os.sep.join(fplist[:-1])
                    filename = fplist[-1]
                    if rel_path.startswith(os.sep):
                        rel_path = rel_path[1:]
                    if (not rel_path.endswith(os.sep)):
                        rel_path = rel_path + os.sep
                    if (not remote_path.endswith(os.sep)):
                        remote_path = remote_path + os.sep
                    sftp.mkdir(remote_path + rel_path)
                    sftp.put(fullpath, remote_path + rel_path + filename)
        elif(local == tgt):
            pass
            # https://www.cnblogs.com/haigege/p/5517422.html





            if os.path.isdir(local):
                for root, paths, filenames in os.walk(local):
                    for filename in filenames:
                        logger.debug(filename)
                        fullpath = root + os.sep + filename
                        logger.debug(filename + ' ' + fullpath)
                        remote_fn = remote + '/' + fullpath.replace(local, '')
                        logger.debug('send ' + fullpath + ' to ' + ip + ' as ' + remote_fn)
                        sftp.put(fullpath, remote_fn)
                    for path in paths:
                        local_path = root + os.sep + path
                        remote_path = remote + '/' + local_path.replace(local, '')
                        logger.debug('create ' + remote_path + ' on ' + ip)
                        sftp.mkdir(remote_path)
                dest = remote
            else:
                dest = remote + '/' + local.split(os.sep)[-1]
                logger.debug('copy ' + local + ' to ' + dest)
                sftp.put(local, dest)
        elif ('r2l' == direction):
            if (not os.path.exists(localpath)):
                os.makedirs(localpath)
            src = remote
            if (local.endswith(os.sep)):
                dest = localpath + os.sep + remote.split(os.sep)[-1]
            else:
                dest = local
            paramiko.SFTPClient.from_transport(t).get(src, dest)
    except Exception as err:
        logger.error(err)
        dest = None
    finally:
        t.close()
    logger.debug('copied as ' + dest)
    return dest


if ('__main__' == __name__):
    print(scan())
    t = paramiko.Transport('192.168.56.101:22')
    t.connect(username='gcd0318', password='12121212')
    sftp = paramiko.SFTPClient.from_transport(t)
    print(deep_scan_remote(sftp, '/home/gcd0318/work'))
    print(get_md5('tasks.py'))
    print(get_md5('.'))
#    print(get_path_size('./'), get_path_size('./cicada.log'))