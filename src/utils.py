from config import DNS, PERIOD_s, ENCRYPT_BLOCK, INCOMING
from const import UTF8, TIMEOUT_s, SHORT_s, RETRY, SCRIPT_EXECUTE_TIMEOUT_s
from model import logger

import paramiko

import glob
import os
import shutil
import socket
import stat
import subprocess
import time

def timestamp(t=None, fmt='%Y%m%d_%H%M%S'):
    if t is None:
        t = time.localtime()
    return time.strftime(fmt, t)


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


def deep_scan(root=INCOMING):
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

def deep_scan_remote(sftp, path=INCOMING):
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

def scan(root=INCOMING):
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
        # use ceil for larger estimation
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
        tmp_path = os.path.abspath('tmp')
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
        path_encrypt = tmp_path + os.sep + pathencrypt.hexdigest()
        with open(path_encrypt, 'w') as tmpf:
#            print(absfp, path_md5, file=tmpf)
            encrypt_d = {}
            for filename in deep_scan(absfp):
                if(filename != absfp):
                    encrypt_d[filename.replace(absfp, '')] = get_encrypt(filename, encrypt=encrypt)
            for k, v in sorted(encrypt_d.items(), key=lambda item:item[0]):
                print(k, v, file=tmpf)
#        print(path_encrypt, os.path.exists(path_encrypt))
        res = get_encrypt(path_encrypt, encrypt=encrypt)
        os.remove(path_encrypt)
#    print('encrypt:', res)
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




def remote_exec(cmd, ip, username, password, port=22, no_err=True, timeout=TIMEOUT_s, short_wait=SHORT_s, retry=RETRY, omit_str=None, platform='linux'):
    resd = {'res': [], 'err': []}
    rt = 0
    if ('' != cmd):
        if ('linux' == platform):
            while (('err' in resd.keys()) and (rt <= retry)):
                resd.pop('err')
                ssh = paramiko.SSHClient()
                try:
                    ssh.load_system_host_keys()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    logger.debug('try to connect to ' + ip + ' via ' + str(port) + ' with username: ' + username)
                    ssh.connect(hostname=ip, port=port, username=username, password=password)
                    if (cmd.split(';')[-1].replace('&', '').split('-')[0].strip() in (
                    'reboot', 'shutdown', 'poweroff')):
                        ssh.exec_command(cmd, timeout=timeout)
                    else:
                        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
                        resd['res'] = stdout.readlines()
                        resd['err'] = stderr.readlines()
                        logger.debug(str(resd))
                        if ((0 == len(resd['err'])) or ((not no_err) and (0 < len(resd['res'])))):
                            resd.pop('err')
                        else:
                            rt = rt + 1
                except Exception as err:
                    import traceback
                    logger.error(str(err))
                    logger.error(traceback.format_exc())
                    resd['err'] = [str(err), traceback.format_exc()]
                    rt = rt + 1
                    time.sleep(short_wait)
                finally:
                    ssh.close()
                logger.debug(str(resd))
                logger.debug(str(no_err))
            if (not 'err' in resd):
                resd['err'] = []
        elif('windows' == platform):
            while (('err' in resd.keys()) and (rt <= retry)):
                resd.pop('err')
                try:
                    ret = winrm.Session('http://' + ip + ':' + str(port) + '/wsman', auth=(username, password)).run_cmd(cmd)
                    resd['res'], resd['err'] = ret.std_out, ret.std_err
                except Exception as err:
                    import traceback
                    logger.error(str(err))
                    logger.error(traceback.format_exc())
                    resd['err'] = [str(err), traceback.format_exc()]
                    rt = rt + 1
                    time.sleep(short_wait)
                finally:
                    pass
    return resd


def exec_cmd(cmd, machine='localhost', username=None, password=None, port=22, no_err=True, omit_str=None, platform='linux'):
    logger.debug('run ' + cmd + ' on ' + machine + ' with no_err as ' + str(no_err))
    rtcode = -1
    resl = []
    if (machine in LOCALS):
        logger.debug('run ' + cmd + ' on localhost')
        rtcode, resl = exec_local_cmd(cmd)
    else:
        logger.debug('remote run ' + cmd + ' on ' + machine)
        resd = remote_exec(cmd, machine, username, password, port, no_err=no_err, timeout=TIMEOUT_s, short_wait=SHORT_s, retry=RETRY, omit_str=omit_str, platform=platform)
        logger.debug('rtcode of exec_cmd ' + cmd + ' is: ' + str(rtcode))
        logger.debug('resd:\n' + str(resd))
        resl = resd['res']
        logger.debug(str('err' in resd))
        logger.debug(str(0 != len(resd['err'])))
        logger.debug(str(not no_err))
        logger.debug(omit_str)
        if (('err' in resd) and (0 != len(resd['err'])))and no_err and ((omit_str is None) or (not (omit_str in resd['res'][0]))):
            resl = resd['err']
        else:
            rtcode = 0
    logger.debug(str(rtcode))
    return rtcode, resl


def run_shell_cmd(cmd):
    logger.info("run cmd: %s", cmd)
    try:
        rc = subprocess.call(cmd, shell=True)
        if rc != 0:
            logger.error("Fail to run %s , rc: %s" % (cmd, rc))
    except OSError as e:
        logger.error("Fail to run cmd: %s" % e)
    return rc


def exec_local_cmd(args, shell=True, with_blank=False):
    logger.debug('run on localhost')
    resl = []
    try:
        process = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        rtcode = process.returncode
        output = stdout + stderr
        process.poll()
        if (0 != rtcode):
            output = stderr
    except OSError as e:
        rtcode = e.errno
        output = "Fail to run command: %s" % e
    for l in output.decode('utf-8').split('\n'):
        if ((0 < len(l)) or with_blank):
            resl.append(l)
    return rtcode, resl


def run_shell_script(args, shell=False, log=logger, timeout=SCRIPT_EXECUTE_TIMEOUT_s, return_output=False):
    command = Command(args)
    return command.run(log=log, shell=shell, timeout=timeout, return_output=return_output)


class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.error_message = None

    def run(self, shell=False, log=logger, timeout=SCRIPT_EXECUTE_TIMEOUT_s, return_output=False):
        try:
            def kill_process():
                if self.process.poll() is None:
                    log.error('Kill process')
                    self.process.kill()
                    self.error_message = "shell process killed by timeout, timeout=%s" % timeout
                    log.error(self.error_message)

            self.process = subprocess.Popen(self.cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            close_fds=True)
            # start timer
            t = threading.Timer(timeout, kill_process)
            t.start()

            # wrap self.process.stdout with a NonBlockingStreamReader object:
            nbsr = NonBlockingStreamReader(self.process.stdout)

            shell_output = ""

            # print the output in real-time
            while self.process.poll() is None:
                line = nbsr.readline(0.1)  # 0.1 secs to let the shell output the result
                if line:
                    shell_output += line
                    log.info(line.rstrip())

            # When the subprocess terminates there might be unconsumed output that still needs to be processed.
            content = nbsr.readline(1)
            if content:
                shell_output += content
                log.info(content)

            # cancel timer
            t.cancel()
            if return_output:
                output = shell_output if self.process.returncode == 0 else self.error_message
                return self.process.returncode, output
            else:
                return self.process.returncode, self.error_message
        except OSError as e:
            error_message = "Fail to run command: %s" % e
            log.error(error_message)
            return e.errno, error_message


class NonBlockingStreamReader:
    def __init__(self, stream):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()

        def _populateQueue(stream, queue):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''

            while True:
                line = stream.readline()
                if line:
                    queue.put(line)
                else:
                    break
                    # raise UnexpectedEndOfStream

        self._t = threading.Thread(target=_populateQueue,
                                   args=(self._s, self._q))
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None,
                               timeout=timeout)
        except Exception as err:
            return None


def execute(command, *args, **kwargs):
    """
    Execute an command then return its return code.
    :type command: str or unicode
    :param timeout: timeout of this command
    :type timeout: int
    :rtype: (int, str, str)
    """

    timeout = kwargs.pop("timeout", None)
    command_list = [command, ]
    command_list.extend(args)

    ref = {
        "process": None,
        "stdout": None,
        "stderr": None,
    }

    def target():
        ref['process'] = subprocess.Popen(
            " ".join(command_list),
            shell=True,
            close_fds=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        ref['stdout'], ref['stderr'] = ref['process'].communicate()

    thread = Thread(target=target)
    thread.start()
    thread.join(timeout=timeout)
    if thread.is_alive():
        if ref['process'] is not None:
            ref['process'].terminate()
            ref['process'].wait()
        thread.join()

    return ref['process'].returncode, ref['stdout'], ref['stderr']


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
    remote_cp(src, 'gcd0318:12121212@10.0.2.15@'+tgt)