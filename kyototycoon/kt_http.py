#!/usr/bin/env python
#
# Copyright 2011, Toru Maesaka
#
# Redistribution and use of this source code is licensed under
# the BSD license. See COPYING file for license description.

from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import base64
import http.client
import struct
import time
from . import kt_error
try:
    from percentcoding import quote, unquote
except ImportError:
    from urllib.parse import quote as _quote
    from urllib.parse import unquote
    quote = lambda s: _quote(s, safe="")

try:
    import pickle as pickle
except ImportError:
    import pickle

# Stick with URL encoding for now. Eventually run a benchmark
# to evaluate what the most approariate encoding algorithm is.
KT_HTTP_HEADER = {
  'Content-Type' : 'text/tab-separated-values; colenc=U',
}

KT_PACKER_CUSTOM = 0
KT_PACKER_PICKLE = 1
KT_PACKER_JSON   = 2
KT_PACKER_STRING = 3

def _dict_to_tsv(dict):
    return '\n'.join(quote(k) + '\t' + quote(str(v)) for (k, v) in list(dict.items()))

def _content_type_decoder(content_type=''):
    ''' Select the appropriate decoding function to use based on the response headers. '''
    if content_type.endswith('colenc=B'):
        return base64.decodestring
    elif content_type.endswith('colenc=U'):
        return unquote
    else:
        return lambda x: x

def _tsv_to_dict(tsv_str, content_type=''):
    decode = _content_type_decoder(content_type)
    rv = {}

    for row in tsv_str.split('\n'):
        kv = row.split('\t')
        if len(kv) == 2:
            rv[decode(kv[0])] = decode(kv[1])
    return rv

def _tsv_to_list(tsv_str, content_type=''):
    decode = _content_type_decoder(content_type)
    rv = []

    for row in tsv_str.split('\n'):
        kv = row.split('\t')
        if len(kv) == 2:
            pair = (decode(kv[0]), decode(kv[1]))
            rv.append(pair)
    return rv


class Cursor(object):
    cursor_id_counter = 1

    def __init__(self, protocol_handler):
        self.protocol_handler = protocol_handler
        self.cursor_id = Cursor.cursor_id_counter
        Cursor.cursor_id_counter += 1

        self.err = kt_error.KyotoTycoonError()
        self.pack = self.protocol_handler.pack
        self.unpack = self.protocol_handler.unpack
        self.pack_type = self.protocol_handler.pack_type

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        # Cleanup the cursor when leaving "with" blocks
        self.delete()

    def jump(self, key=None, db=None):
        path = '/rpc/cur_jump'
        if db:
            db = quote(db)
            path += '?DB=' + db

        request_dict = {}
        request_dict['CUR'] = self.cursor_id
        if key:
            request_dict['key'] = key

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def jump_back(self, key=None, db=None):
        path = '/rpc/cur_jump_back'
        if db:
            db = quote(db)
            path += '?DB=' + db

        request_dict = {}
        request_dict['CUR'] = self.cursor_id
        if key:
            request_dict['key'] = key

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def step(self):
        path = '/rpc/cur_step'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def step_back(self):
        path = '/rpc/cur_step_back'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def set_value(self, value, step=False, xt=None):
        path = '/rpc/cur_set_value'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id
        request_dict['value'] = self.pack(value)
        if step:
            request_dict['step'] = True
        if xt:
            request_dict['xt'] = xt

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def remove(self):
        path = '/rpc/cur_remove'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def get_key(self, step=False):
        path = '/rpc/cur_get_key'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id
        if step:
            request_dict['step'] = True

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return _tsv_to_dict(body, res.getheader('Content-Type', ''))['key']

    def get_value(self, step=False):
        path = '/rpc/cur_get_value'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id
        if step:
            request_dict['step'] = True

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return self.unpack(_tsv_to_dict(body, res.getheader('Content-Type', ''))['value'])

    def get(self, step=False):
        path = '/rpc/cur_get'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id
        if step:
            request_dict['step'] = True

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status == 404:
            self.err.set_error(self.err.NOTFOUND)
            return None, None

        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False, False

        self.err.set_success()
        res_dict = _tsv_to_dict(body, res.getheader('Content-Type', ''))
        key = res_dict['key']
        value = self.unpack(res_dict['value'])
        return key, value

    def seize(self):
        path = '/rpc/cur_seize'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        res_dict = _tsv_to_dict(body, res.getheader('Content-Type', ''))
        res_dict['key'] = res_dict['key']
        res_dict['value'] = self.unpack(res_dict['value'])
        return res_dict

    def delete(self):
        path = '/rpc/cur_delete'

        request_dict = {}
        request_dict['CUR'] = self.cursor_id

        request_body = _dict_to_tsv(request_dict)
        self.protocol_handler.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.protocol_handler.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True



class ProtocolHandler(object):
    def __init__(self, pack_type=KT_PACKER_PICKLE, pickle_protocol=2):
        self.err = kt_error.KyotoTycoonError()
        self.pickle_protocol = pickle_protocol
        self.pack_type = pack_type

        if self.pack_type == KT_PACKER_PICKLE:
            self.pack = self._pickle_packer
            self.unpack = self._pickle_unpacker

        elif self.pack_type == KT_PACKER_STRING:
            self.pack = lambda data: data
            self.unpack = lambda data: data

        else:
            raise Exception('unknown pack type specified')

    def error(self):
        return self.err

    def cursor(self):
        return Cursor(self)

    def open(self, host, port, timeout):
        # Save connection parameters so the connection can be re-established
        # on "Connection: close" response.
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.conn = http.client.HTTPConnection(host, port, timeout=timeout)
        except Exception as e:
            raise e
        return True

    def close(self):
        try:
            self.conn.close()
        except Exception as e:
            raise e
        return True

    def getresponse(self):
        res = self.conn.getresponse()
        body = res.read()

        if res.will_close:
            self.conn.close()
            self.open(self.host, self.port, self.timeout)

        return res, body

    def echo(self):
        self.conn.request('POST', '/rpc/echo')

        res, body = self.getresponse()
        if res.status != 200:
           self.err.set_error(self.err.EMISC)
           return False

        self.err.set_success()
        return True

    def get(self, key, db=None):
        if key is None:
            return False

        path = key
        if db:
            path = '/%s/%s' % (db, key)
        path = quote(path.encode('UTF-8'))

        self.conn.request('GET', path)
        res, body = self.getresponse()

        if res.status == 404:
            self.err.set_error(self.err.NOTFOUND)
            return None
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return self.unpack(body)

    def set_bulk(self, kv_dict, expire, atomic, db):
        if not isinstance(kv_dict, dict):
            return False

        if len(kv_dict) < 1:
            self.err.set_error(self.err.LOGIC)
            return False

        path = '/rpc/set_bulk'
        if db:
            db = quote(db)
            path += '?DB=' + db

        request_body = ''

        if atomic:
            request_body = 'atomic\t\n'

        for k, v in list(kv_dict.items()):
            k = quote(k)
            v = quote(self.pack(v))
            request_body += '_' + k + '\t' + v + '\n'

        self.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return int(_tsv_to_dict(body, res.getheader('Content-Type', ''))['num'])

    def remove_bulk(self, keys, atomic, db):
        if not hasattr(keys, '__iter__'):
            self.err.set_error(self.err.LOGIC)
            return 0

        request_header = ''
        if atomic:
            request_header = 'atomic\t\n'

        request_body = ''
        for key in keys:
            request_body += '_' + quote(key) + '\t\n'
        if len(request_body) < 1:
            self.err.set_error(self.err.LOGIC)
            return 0

        path = '/rpc/remove_bulk'
        if db:
            db = quote(db)
            path += '?DB=' + db
        self.conn.request('POST', path, body=request_header + request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return int(_tsv_to_dict(body, res.getheader('Content-Type', ''))['num'])

    def get_bulk(self, keys, atomic, db):
        if not hasattr(keys, '__iter__'):
            self.err.set_error(self.err.LOGIC)
            return None

        request_header = ''
        if atomic:
            request_header = 'atomic\t\n'

        request_body = ''
        for key in keys:
            request_body += '_' + quote(key) + '\t\n'

        if len(request_body) < 1:
            self.err.set_error(self.err.LOGIC)
            return {}

        path = '/rpc/get_bulk'
        if db:
            db = quote(db)
            path += '?DB=' + db
        self.conn.request('POST', path, body=request_header + request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return None

        rv = {}
        res_dict = _tsv_to_dict(body, res.getheader('Content-Type', ''))
        n = res_dict.pop('num')

        if n == '0':
            self.err.set_error(self.err.NOTFOUND)
            return {}

        for k, v in list(res_dict.items()):
            if v is not None:
                rv[k[1:]] = self.unpack(v)

        self.err.set_success()
        return rv

    def get_int(self, key, db=None):
        if key is None:
            self.err.set_error(self.err.LOGIC)
            return False

        path = key
        if db:
            path = '/%s/%s' % (db, key)
        path = quote(path.encode('UTF-8'))

        self.conn.request('GET', path)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.NOTFOUND)
            return None

        self.err.set_success()
        return struct.unpack('>q', body)[0]

    def vacuum(self, db):
        path = '/rpc/vacuum'

        if db:
            db = quote(db)
            path += '?DB=' + db

        self.conn.request('GET', path)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)

        self.err.set_success()
        return res.status == 200

    def match_prefix(self, prefix, max, db):
        if prefix is None:
            self.err.set_error(self.err.LOGIC)
            return None

        rv = []
        request_dict = {}
        request_dict['prefix'] = prefix

        if max:
            request_dict['max'] = max
        if db:
            request_dict['DB'] = db

        request_body = _dict_to_tsv(request_dict)
        self.conn.request('POST', '/rpc/match_prefix',
                          body=request_body, headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        res_list = _tsv_to_list(body, res.getheader('Content-Type', ''))
        if len(res_list) == 0 or res_list[-1][0] != 'num':
            self.err.set_err(self.err.EMISC)
            return False
        num_key, num = res_list.pop()
        if num == '0':
            self.err.set_error(self.err.NOTFOUND)
            return []

        for k, v in res_list:
            rv.append(k[1:])

        self.err.set_success()
        return rv

    def match_prefix_range(self, prefix, start, max, backward=False, db=None):
        if prefix is None:
            self.err.set_error(self.err.LOGIC)
            return None

        rv = []
        request_dict = {}
        request_dict['prefix'] = prefix
        request_dict['start'] = start

        if max:
            request_dict['max'] = max
        if db:
            request_dict['DB'] = db
        if backward:
            request_dict['backward'] = 1

        request_body = _dict_to_tsv(request_dict)
        self.conn.request('POST', '/rpc/match_prefix_range',
                          body=request_body, headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        res_list = _tsv_to_list(body, res.getheader('Content-Type', ''))
        if len(res_list) == 0 or res_list[-1][0] != 'num':
            self.err.set_err(self.err.EMISC)
            return False
        num_key, num = res_list.pop()
        if num == '0':
            self.err.set_error(self.err.NOTFOUND)
            return []

        for k, v in res_list:
            rv.append(k[1:])

        self.err.set_success()
        return rv

    def match_regex(self, regex, max, db):
        if regex is None:
            self.err.set_error(self.err.LOGIC)
            return None

        path = '/rpc/match_regex'
        if db:
            path += '?DB=' + db

        request_dict = { 'regex': regex }
        if max:
            request_dict['max'] = max

        request_body = _dict_to_tsv(request_dict)
        self.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return None

        rv = []
        res_list = _tsv_to_list(body, res.getheader('Content-Type', ''))
        if len(res_list) == 0 or res_list[-1][0] != 'num':
            self.err.set_err(self.err.EMISC)
            return False
        num_key, num = res_list.pop()
        if num == '0':
            self.err.set_error(self.err.NOTFOUND)
            return []

        for k, v in res_list:
            rv.append(k[1:])

        self.err.set_success()
        return rv

    def set(self, key, value, expire, db):
        if key is None:
            self.err.set_error(self.err.LOGIC)
            return False

        if db:
            key = '/%s/%s' % (db, key)
        key = quote(key.encode('UTF-8'))
        value = self.pack(value)

        self.err.set_success()

        status = self._rest_put('set', key, value, expire)
        if status != 201:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def add(self, key, value, expire, db):
        if key is None:
            self.err.set_error(self.err.LOGIC)
            return False

        if db:
            key = '/%s/%s' % (db, key)

        key = quote(key.encode('UTF-8'))
        value = self.pack(value)
        status = self._rest_put('add', key, value, expire)

        if status != 201:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def cas(self, key, old_val, new_val, expire, db):
        if key is None:
            self.err.set_error(self.err.LOGIC)
            return False

        path = '/rpc/cas'
        if db:
            path += '?DB=' + db

        request_dict = { 'key': key }

        if old_val:
            request_dict['oval'] = self.pack(old_val)
        if new_val:
            request_dict['nval'] = self.pack(new_val)
        if expire:
            request_dict['xt'] = expire

        request_body = _dict_to_tsv(request_dict)

        self.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def remove(self, key, db):
        if key is None:
            self.err.set_error(self.err.LOGIC)
            return False

        if db:
            key = '/%s/%s' % (db, key)

        key = quote(key.encode('UTF-8'))
        self.conn.request('DELETE', key)

        res, body = self.getresponse()
        if res.status != 204:
            self.err.set_error(self.err.NOTFOUND)
            return False

        self.err.set_success()
        return True

    def replace(self, key, value, expire, db):
        if key is None:
            self.err.set_error(self.err.LOGIC)
            return False

        if db:
            key = '/%s/%s' % (db, key)

        key = quote(key.encode('UTF-8'))
        value = self.pack(value)
        status = self._rest_put('replace', key, value, expire)

        if status != 201:
            self.err.set_error(self.err.NOTFOUND)
            return False

        self.err.set_success()
        return True

    def append(self, key, value, expire, db):
        self.err.set_error(self.err.LOGIC)
        if key is None:
            return False
        elif not isinstance(value, str):
            return False

        # Only handle Pickle for now.
        if self.pack_type == KT_PACKER_PICKLE:
            data = self.get(key)
            if data is None:
                data = value
            else:
                data = data + value

            if self.set(key, data, expire, db) is True:
                self.err.set_success()
                return True

        self.err.set_error(self.err.EMISC)
        return False

    def increment(self, key, delta, expire, db):
        if key is None:
            self.err.set_error(self.err.LOGIC)
            return False

        path = '/rpc/increment'
        if db:
            path += '?DB=' + db

        delta = int(delta)
        request_body = 'key\t%s\nnum\t%d\n' % (key, delta)
        self.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return None

        self.err.set_success()
        return int(_tsv_to_dict(body, res.getheader('Content-Type', ''))['num'])

    def increment_double(self, key, delta, expire, db):
        if key is None:
            self.err.set_error(self.err.LOGIC)
            return False

        path = '/rpc/increment_double'
        if db:
            path += '?DB=' + db

        delta = float(delta)
        request_body = 'key\t%s\nnum\t%f\n' % (key, delta)
        self.conn.request('POST', path, body=request_body,
                          headers=KT_HTTP_HEADER)

        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return None

        self.err.set_success()
        return float(_tsv_to_dict(body, res.getheader('Content-Type', ''))['num'])

    def report(self):
        self.conn.request('GET', '/rpc/report')
        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return None

        self.err.set_success()
        return _tsv_to_dict(body, res.getheader('Content-Type', ''))

    def status(self, db=None):
        url = '/rpc/status'

        if db:
            db = quote(db)
            url += '?DB=' + db

        self.conn.request('GET', url)
        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return None

        self.err.set_success()
        return _tsv_to_dict(body, res.getheader('Content-Type', ''))

    def clear(self, db=None):
        url = '/rpc/clear'

        if db:
            db = quote(db)
            url += '?DB=' + db

        self.conn.request('GET', url)
        res, body = self.getresponse()
        if res.status != 200:
            self.err.set_error(self.err.EMISC)
            return False

        self.err.set_success()
        return True

    def count(self, db=None):
        st = self.status(db)
        if st is None:
            return None
        return int(st['count'])

    def size(self, db=None):
        st = self.status(db)
        if st is None:
            return None
        return int(st['size'])

    def _rest_put(self, operation, key, value, expire):
        headers = { 'X-Kt-Mode' : operation }
        if expire != None:
            expire = int(time.time()) + expire;
            headers["X-Kt-Xt"] = str(expire)

        self.conn.request('PUT', key, value, headers)
        res, body = self.getresponse()
        return res.status

    def _pickle_packer(self, data):
        return pickle.dumps(data, self.pickle_protocol)

    def _pickle_unpacker(self, data):
        return pickle.loads(data)
