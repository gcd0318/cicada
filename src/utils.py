from config import DNS, DEF_PATHS, PERIOD_s, ENCRYPT_BLOCK
from const import UTF8
from model import logger

import paramiko

import glob
import os
import shutil
import socket
import stat
import time


def get_func(f):
    def _wrapper(*argc, **kwargs):
        logger.info('running ' + f.__name__)
        while True:
            try:
                f(*argc, **kwargs)
            except Exception as err:
                import traceback
                logger.error(f.__name__)
                logger.error(str(err))
                logger.error(traceback.format_exc())
            time.sleep(PERIOD_s)
    return _wrapper

def is_dir(path, sock=None, sftp=None):
    res = False
    if (sock is None) and (sftp is None) and (not '@' in path):
        res = os.path.isdir(path)
    else:
        username = None
        password = None
        try:
            if ('@' in path):
                auth, sock, remote_path = path.split('@')
                username, password = auth.split(':')
                if not (':' in sock):
                    sock = sock + ':22'
            else:
                remote_path = path
            if sock is not None:
                t = paramiko.Transport(sock)
                t.connect(username=username, password=password)
                sftp = paramiko.SFTPClient.from_transport(t)
            res = stat.S_ISDIR(sftp.lstat(remote_path).st_mode)
        except Exception as err:
            logger.error(__name__)
            logger.error(err)
    return res

def pathize(filepath, force=False):
    if os.path.isdir(filepath) or force:
        tmp = filepath.replace(os.sep+os.sep, os.sep)
        while(tmp != filepath):
            filepath, tmp = tmp, filepath.replace(os.sep+os.sep, os.sep)
        if not (filepath.endswith(os.sep)):
            filepath = filepath + os.sep
    return filepath


def deep_scan(root=DEF_PATHS['INCOMING']):
    resl = []
    root = os.path.abspath(root)
    if os.path.isdir(root):
        root = pathize(root)
        for dirpath, dirnames, filenames in os.walk(root):
            if ([] == filenames):
                filenames.append('')
            for filepath in filenames:
                resl.append(os.path.join(dirpath, filepath))
    else:
        resl.append(root)
    return resl

def deep_scan_remote(sftp, path=DEF_PATHS['INCOMING']):
    res = []
    if is_dir(path=path, sftp=sftp):
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
        root = pathize(root)
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
            logger.error(__name__)
            logger.error(err)
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

def get_encrypt(filepath, encrypt='sha512'):
    res = None
    from hashlib import sha512 as encrypt_func
    if('md5' == encrypt):
        from hashlib import md5 as encrypt_func
    absfp = os.path.abspath(filepath)
    if os.path.isfile(absfp):
        m = encrypt_func()
#        m.update(absfp.encode(UTF8))
        with open(absfp, 'rb') as f:
            b = f.read(ENCRYPT_BLOCK)
            while(b):
                m.update(b)
                b = f.read(ENCRYPT_BLOCK)
            res = m.hexdigest()
    elif os.path.isdir(absfp):
        absfp = pathize(absfp)
        pathencrypt = encrypt_func()
        pathencrypt.update(absfp.encode(UTF8))
        path_encrypt = pathencrypt.hexdigest()
        with open(path_encrypt, 'w') as tmpf:
#            print(absfp, path_md5, file=tmpf)
            encrypt_d = {}
            for filename in deep_scan(absfp):
                if(filename != absfp):
                    encrypt_d[filename.replace(absfp, '')] = get_encrypt(filename, encrypt=encrypt)
            for k, v in sorted(encrypt_d.items(), key=lambda item:item[0]):
                print(k, v, file=tmpf)
        res = get_encrypt(path_encrypt, encrypt=encrypt)
        os.remove(path_encrypt)
    return res

def remote_mkdir(sftp, path):
    path_split = path.split(os.sep)
    paths = []
    i = 0
    remote_path = os.sep.join(path_split[:len(path_split) - i])
    while (i < len(path_split))and (not(is_dir(sftp=sftp, path=remote_path))):
#        print(remote_path, is_dir(sftp=sftp, path=remote_path))
        paths.append(remote_path)
        i = i + 1
        remote_path = os.sep.join(path_split[:len(path_split) - i])
    while (0 < len(paths)):
        sftp.mkdir(paths.pop())


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
    res = None
    try:
        logger.debug('copy from ' + src + ' to ' + tgt)
        src_root = ''
        tgt_root = ''
        local = os.path.abspath(local)
        logger.debug('local file is as ' + local)
        if (local == src):
            tgt_path = remote_path
            if os.path.isdir(src):
                src_files = deep_scan(src)
                if src.endswith(os.sep):
                    src_root = src.split(os.sep)[-2]
                else:
                    src_root = src.split(os.sep)[-1]
                while tgt_path.endswith(os.sep):
                    tgt_path = tgt_path[:-1]
                tgt_path = os.sep.join([tgt_path, src_root, ''])
            else:
                src_files = [src]
                if is_dir(sftp=sftp, path=tgt_path):
                    pass
            for fullpath in src_files:
                rel_path = ''
                if is_dir(src):
                    fplist = fullpath.replace(src, '').split(os.sep)
                    rel_path = os.sep.join(fplist[:-1])
                    filename = fplist[-1]
                else:
                    filename = fullpath.split(os.sep)[-1]
                while rel_path.startswith(os.sep):
                    rel_path = rel_path[1:]
                if (not tgt_path.endswith(os.sep)):
                    tgt_path = tgt_path + os.sep
                remotepath = tgt_path + rel_path
                if not(remotepath.endswith(os.sep)):
                    remotepath = remotepath + os.sep
                if not(is_dir(sftp=sftp, path=remotepath)):
                    sftp.mkdir(remotepath)
                if not(is_dir(path=fullpath)):
                    sftp.put(fullpath, remotepath + filename)
        elif(remote == src):
            src_root = ''
            src_path = remote_path
            if is_dir(sftp=sftp, path=src_path):
                src_files = deep_scan_remote(sftp, src_path)
                if src_path.endswith(os.sep):
                    src_root = src_path.split(os.sep)[-2]
                else:
                    src_root = src_path.split(os.sep)[-1]
            else:
                src_files = [src_path]
                src_path = os.sep.join(src_path.split(os.sep)[:-1])
            for fullpath in src_files:
                fplist = fullpath.replace(src_path, '').split(os.sep)
                rel_path = os.sep.join(fplist[:-1])
                filename = fplist[-1]
                if rel_path.startswith(os.sep):
                    rel_path = rel_path[1:]
                if (not local.endswith(os.sep)):
                    local = local + os.sep
                localpath = local + src_root + os.sep + rel_path
                if not(localpath.endswith(os.sep)):
                    localpath = localpath + os.sep
                if not(os.path.exists(localpath)):
                    os.mkdir(localpath)
                if not(is_dir(sftp=sftp, path=fullpath)):
                    sftp.get(fullpath, localpath + filename)
        logger.debug(src + ' is copied to ' + tgt)
        res = tgt + os.sep + src_root
    except Exception as err:
        logger.error(__name__)
        logger.error(err)
        import traceback
        logger.error(traceback.format_exc())
        res = None
    finally:
        t.close()
    return res

def is_same(src, tgt):
    src = pathize(os.path.abspath(src))
    tgt = pathize(os.path.abspath(tgt))
    res = True
    if os.path.isdir(src):
        if os.path.isdir(tgt):
            fps = scan(src)
            i = 0
            while(res and (i < len(fps))):
                fp = fps[i]
                tail = fp.replace(src, '')
                if('' != res):
                    res = res and is_same(fp, tgt+tail)
                i = i + 1
        else:
            res = False
            if not res:
                print(src, tgt)
    else:
        if os.path.isdir(tgt):
            res = (get_encrypt(src) == get_encrypt(tgt + src.split(os.sep)[-1]))
            if not res:
                print(src, tgt)
        else:
            res = (get_encrypt(src) == get_encrypt(tgt))
            if not res:
                print(src, tgt)
    return res

def local_cp(src, tgt):
    src = pathize(os.path.abspath(src))
    tgt = pathize(os.path.abspath(tgt))
    if os.path.isdir(src):
        if os.path.isdir(tgt):
            for fp in scan(src):
                tgt_fp = tgt + fp.replace(src, '')
                if os.path.isdir(fp):
                    if not os.path.exists(tgt_fp):
                        os.mkdir(tgt_fp)
                local_cp(fp, tgt_fp)
        else:
            tgt = None
    else:
        if os.path.isdir(tgt):
            tgt = tgt + src.split(os.sep)[-1]
        else:
            if os.path.exists(tgt):
                os.remove(tgt)
        tgt = shutil.copy2(src, tgt)
    return tgt



if ('__main__' == __name__):
#    src = ''
#    print(scan())
#    t = paramiko.Transport('10.50.180.56:10022')
#    t.connect(username='guochen', password='12121212')
#    sftp = paramiko.SFTPClient.from_transport(t)
#    print(is_dir(path='/home/guochen/downloads', sftp=sftp))
#    print(deep_scan_remote(sftp, '/home/guochen/downloads'))
#    print(deep_scan_remote(sftp, '/home/guochen/downloads/crontab.log'))
#    print(is_dir(path='/home/guochen/downloads'))
#    print(is_dir(path='guochen:12121212@10.50.180.56:10022@/home/guochen/downloads/crontab.log'))
#    print(remote_cp('guochen:12121212@10.50.180.56:10022@/home/guochen/downloads', os.path.abspath('.')))
#    print(remote_cp('guochen:12121212@10.50.180.56:10022@/home/guochen/downloads/crontab.log', os.path.abspath('.')))
#    print(remote_cp('/home/gcd0318/downloads', 'guochen:12121212@10.50.180.56:10022@/home/guochen'))
#    print(remote_cp('/home/gcd0318/downloads/crontab.log', 'guochen:12121212@10.50.180.56:10022@/home/guochen'))
#    print(get_encrypt('tasks.py'))
#    print(get_encrypt('d:/cn_windows_10_consumer_edition_version_1809_updated_sept_2018_x64_dvd_051b7719.iso', encrypt='sha512'))
#    print(get_encrypt('.', encrypt='sha512'))
#    print(get_path_size('./'), get_path_size('./cicada.log'))
#    print(is_same('/mnt/sda1/incoming/test', '/mnt/sda1/incoming/newtest'))
    src, tgt = '/mnt/sda1/incoming', '/mnt/sda1/backup'
    print(local_cp(src, tgt))
    print(is_same(src, tgt))
    print(get_encrypt(src), get_encrypt(tgt))