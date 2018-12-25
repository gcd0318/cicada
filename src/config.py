CLUSTER = ['192.168.56.101', '10.0.2.15']

HTTP_PORT = 9999

ROOT = '/mnt/sda1/'
DEF_PATHS = {
    'INCOMING': ROOT + 'incoming/',
    'BACKUP': ROOT + 'backup/'
}

class DefaultPaths():
    ROOT = '/mnt/sda1/'
    INCOMING = ROOT + 'incoming/'
    BACKUP = ROOT + 'backup/'

COPIES = 2

DNS = ['192.168.75.21', '8.8.8.8', '4.4.4.4', '114.114.114.114']

MIN_FREE_SPACE = 100 * 1024 * 1024 # 100MB

TIMEOUT = 60
PERIOD_s = 1