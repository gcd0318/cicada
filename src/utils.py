from config import DNS, DEF_PATHS, PERIOD_s
from const import UTF8
from model import logger

from hashlib import md5

import glob
import os
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
            for filepath in filenames:
                resl.append(os.path.join(dirpath, filepath))
    else:
        resl.append(root)
    return resl

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


if ('__main__' == __name__):
    print(get_md5('tasks.py'))
    print(get_md5('.'))
#    print(get_path_size('./'), get_path_size('./cicada.log'))