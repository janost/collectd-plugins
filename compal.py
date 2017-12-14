from __future__ import with_statement
from __future__ import absolute_import
import urlparse
from collections import OrderedDict
from lxml import etree
import requests
import collectd

MODEM_IP = '192.168.100.1'
MODEM_PASSWORD = ''
COMPAL_MONITOR = None

class Compal(object):
    def __init__(self, router_ip, key=None, timeout=10):
        self.parser = etree.XMLParser(recover=True)
        self.router_ip = router_ip
        self.timeout = timeout
        self.key = key

        self.session = requests.Session()
        self.session.max_redirects = 3

        self.session.hooks['response'].append(self.token_handler)
        self.session_token = None
        self.initial_res = self.get('/common_page/login.html')

    def url(self, path):
        while path.startswith('/'):
            path = path[1:]

        return "http://{ip}/{path}".format(ip=self.router_ip, path=path)

    def token_handler(self, res, *args, **kwargs):
        self.session_token = res.cookies.get('sessionToken')

    def post(self, path, _data, **kwargs):
        data = OrderedDict()
        data['token'] = self.session_token

        if 'fun' in _data:
            data['fun'] = _data.pop('fun')

        data.update(_data)

        res = self.session.post(self.url(path), data=data,
                                allow_redirects=False, timeout=self.timeout,
                                **kwargs)

        return res

    def post_binary(self, path, binary_data, filename, **kwargs):
        headers = {
            'Content-Disposition':
                'form-data; name="file"; filename="%s"' % filename,  # noqa
            'Content-Type': 'application/octet-stream'
        }
        self.session.post(self.url(path), data=binary_data, headers=headers,
                          **kwargs)

    def get(self, path, **kwargs):
        res = self.session.get(self.url(path), timeout=self.timeout, **kwargs)

        self.session.headers.update({'Referer': res.url})
        return res

    def xml_getter(self, fun, params):
        params['fun'] = fun

        return self.post('/xml/getter.xml', params)

    def xml_setter(self, fun, params=None):
        params['fun'] = fun

        return self.post('/xml/setter.xml', params)

    def login(self, key=None):
        res = self.xml_setter(15, OrderedDict([
            ('Username', 'admin'),
            ('Password', key if key else self.key)
        ]))

        if res.status_code != 200:
            if res.headers['Location'].endswith(
                    'common_page/Access-denied.html'):
                raise ValueError('Access denied. '
                                 'Still logged in somewhere else?')
            else:
                raise ValueError('Login failed for unknown reason!')

        tokens = urlparse.parse_qs(res.text)

        token_sids = tokens.get('SID')
        if not token_sids:
            raise ValueError('No valid session-Id received! Wrong password?')

        token_sid = token_sids[0]

        self.session.cookies.update({'SID': token_sid})

        return res

    def upstream(self): # The modem is capable of driving 8 upstream channels
        usp = {}
        res = self.xml_getter(11, {})
        xml = etree.fromstring(res.content, parser=self.parser)
        for upstream in xml:
            if upstream.tag == 'upstream':
                cid = upstream.find('usid').text
                cpow = upstream.find('power').text
                usp[cid] = int(cpow)

        usp_values = []
        for x in range(1, 9):
            if str(x) in usp.keys():
                usp_values.append(usp[str(x)])
            else:
                usp_values.append(-100)

        return usp_values

    def downstream(self): # The modem is capable of driving 24 downstream channels
        dsp = {}
        dsn = {}
        res = self.xml_getter(10, {})
        xml = etree.fromstring(res.content, parser=self.parser)
        for downstream in xml:
            if downstream.tag == 'downstream':
                cid = downstream.find('chid').text
                cpow = downstream.find('pow').text
                csnr = downstream.find('snr').text
                dsp[cid] = int(cpow)
                dsn[cid] = int(csnr)

        dsp_values = []
        dsn_values = []
        for x in range(1, 25):
            if str(x) in dsp.keys():
                dsp_values.append(dsp[str(x)])
                dsn_values.append(dsn[str(x)])
            else:
                dsp_values.append(-100)
                dsn_values.append(-100)

        return (dsp_values, dsn_values)

    def logout(self):
        return self.xml_setter(16, {})

def log_info(msg):
    collectd.info('COMPAL: ' + msg)

def log_warn(msg):
    collectd.warning('COMPAL: ' + msg)

def log_err(msg):
    collectd.error('COMPAL: ' + msg)

def read_config(config):
    for node in config.children:
        key = node.key.lower()
        val = node.values[0]

        if key == 'ip':
            log_info('Modem IP set to: %s' % val)
            global MODEM_IP
            MODEM_IP = val
        elif key == 'password':
            log_info('Modem password set.')
            global MODEM_PASSWORD
            MODEM_PASSWORD = val
        else:
            log_info('Unknown config key "%s"' % key)

def compal_init():
    log_info('Setting up Compal monitoring...')
    global COMPAL_MONITOR
    try:
        COMPAL_MONITOR = Compal(MODEM_IP, MODEM_PASSWORD)
        COMPAL_MONITOR.login()
    except Exception as e:
        log_err('Failed to log into the modem: %s' % e)
        COMPAL_MONITOR = None

def read_data():
    global COMPAL_MONITOR
    if COMPAL_MONITOR is None:
        log_warn('Attempting to log in to the modem again...')
        compal_init()

    if COMPAL_MONITOR is not None:
        try:
            usp = COMPAL_MONITOR.upstream()
            dsp, dsn = COMPAL_MONITOR.downstream()
            generate_metrics(usp, dsp, dsn)
        except Exception as e:
            log_err('Failed to get modem data: %s. Attempting to recover.' % e)
            COMPAL_MONITOR = None

def shutdown():
    if COMPAL_MONITOR is not None:
        log_info('Logging out from the modem...')
        COMPAL_MONITOR.logout()

def generate_metrics(usp, dsp, dsn):
    v = collectd.Values(plugin='compal', type='compal')
    v.dispatch(values=usp + dsp + dsn)

collectd.register_config(read_config)
collectd.register_read(read_data)
collectd.register_init(compal_init)
collectd.register_shutdown(shutdown)
