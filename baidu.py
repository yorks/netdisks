#!/usr/bin/env python2
#-*- coding: utf-8 -*-

import urllib2
import urllib
import os
import sys
import re
import getopt
import copy
import time
import random
import json
import base64


import cookie_db
from  utils import PAN
from  utils import sizeof_fmt

verbose=False


class BAIDU(PAN):
    def __init__(self, cookie=None):
        server='http://pan.baidu.com'
        PAN.__init__(self, server, cookie)


    def check_login(self):
        url = self.server + '/disk/home'
        conn = self._request( url )
        html = conn.read()
        try:
            self.user['uk'] = re.findall('"uk":([0-9]+),', html)[0]
            self.user['username'] = re.findall('"username":"([^"]+)"', html)[0]
            self.user['bdstoken'] = re.findall('"bdstoken":"([^"]+)"', html)[0]
            self.user['sign1']    = re.findall('"sign1":"([^"]+)"', html)[0]
            self.user['sign3']    = re.findall('"sign3":"([^"]+)"', html)[0]
            self.user['XDUSS']    = re.findall('"XDUSS":"([^"]+)"', html)[0]
            self.user['timestamp']= int(re.findall('"timestamp":([0-9]+),', html)[0])
            self.user['sign'] = self.sign2()
        except Exception, e:
            print html
            print e
            return False
        url1 = 'https://pcs.baidu.com/rest/2.0/pcs/file?method=plantcookie&type=ett'
        #rl2 = 'https://pcs.baidu.com/rest/2.0/pcs/file?method=plantcookie&type=stoken&source=pcs'
        #rl3 = 'https://pcsdata.baidu.com/rest/2.0/pcs/file?method=plantcookie&type=stoken&source=pcsdata'
        conn1 = self._request(url1)
        #conn2 = self._request(url2)
        #onn3 = self._request(url3)
        pcsett = conn1.headers['set-cookie'].split()[0]
        self.headers['Cookie'] = self.headers['Cookie']+' '+pcsett
        #print self.headers
        #rint conn2.headers
        #rint conn3.headers

        return self.user

    def _get_tmp_one_fid(self):
        ret=''
        try:
            ret = self.list_file('/tmp/', retonly=True)
            flist = ret['list']
        except Exception, e:
            print e
            print ret
        for f in flist:
            if f['isdir'] == 0:
                return f['fs_id']
        return False
    def check_sign(self):
        fid = self._get_tmp_one_fid()
        if not fid:
            print "/tmp/ 目录下面找不到文件 请确认/tmp/目录下面有至少一个文件."
            return False
        cnt=1
        while 1:
            if cnt > 20:
                print "check sign 20 times, give up."
                return False
            if bd.get_dlink(fid):
                return True
            else:
                time.sleep(1)
                if not bd.check_login():
                    print "失败，获取首页的sign1 sign3信息出错."
                    return False
            print "正在进行第 %d 次检查 sign2"% cnt
            cnt = cnt + 1


    def sign2(self, s3=None, s1=None):
        if not s3:
            s3 = self.user['sign3']
        if not s1:
            s1 = self.user['sign1']

        o = ""
        v = len(s3)
        a = [ord(s3[i % v]) for i in range(256)]
        p = range(256)
        # loop one
        u = 0
        for q in range(256):
            u = (u + p[q] + a[q]) % 256
            p[q], p[u] = p[u], p[q]
        # loop two
        i = u = 0
        for q in range(len(s1)):
            i = (i + 1) % 256
            u = (u + p[i]) % 256
            p[i], p[u] = p[u], p[i]
            k = p[((p[i] + p[u]) % 256)]
            o += chr(ord(s1[q]) ^ k)
        return base64.b64encode(o).decode('utf-8')

    def list_file(self, path='/', retonly=False):
        path = urllib.quote( path )
        url = self.server+'/api/list?channel=chunlei&clienttype=0&web=1&num=100&page=1&dir='+path+'&order=time&desc=1&showempty=0&_=1415186792830&bdstoken='+self.user['bdstoken']+'&channel=chunlei&clienttype=0&web=1&app_id=250528'

        conn = self._request( url )
        html = conn.read()
        foo = json.loads( html )
        for f in foo['list']:
            if not retonly:print f['path']
        return foo

    def list_offline_download(self):
        url = self.server + '/rest/2.0/services/cloud_dl?bdstoken='+self.user['bdstoken']+'&need_task_info=1&status=255&start=0&limit=10&method=list_task&app_id=250528&t=1415191187214&channel=chunlei&clienttype=0&web=1'
        conn = self._request( url )
        html = conn.read()
        foo = json.loads( html )
        for t in foo['task_info']:
            print t['task_name'], t['status']
        return foo

    def add_offline_task(self, surl, save_path='/'):
        url = self.server + '/rest/2.0/services/cloud_dl?bdstoken='+self.user['bdstoken']+'&channel=chunlei&clienttype=0&web=1&app_id=250528'
        data = {'method':'add_task',
                'file_sha1':'',
                'save_path':save_path,
                'selected_idx':'0',
                'task_from':'1',
                't':'1415191868354',
                'source_url':surl,
                'type':'4',
                }
        pdata = urllib.urlencode( data )
        conn = self._request( url, pdata )
        print conn.read()

    def quota(self):
        url = self.server + '/api/quota?bdstoken='+self.user['bdstoken']+'&channel=chunlei&clienttype=0&web=1&app_id=250528'
        data = {'method':'quota'}
        pdata = urllib.urlencode( data )
        conn  = self._request(url, pdata)
        jdata = json.loads( conn.read() )
        ''' {"errno":0,"used":431477856150,"total":2322818138112,"request_id":9045033441787514765} '''
        try:
            print sizeof_fmt( jdata['used'] ), '/', sizeof_fmt( jdata['total'] )
        except Exception, e:
            print e
            print jdata

    def meta(self, file_path):
        file_list = []
        file_list.append( file_path )
        url = self.server + '/api/filemetas?blocks=0&dlink=1&method=filemetas&channel=chunlei&clienttype=0&web=1&app_id=250528&bdstoken='+self.user['bdstoken']
        data = {'target':json.dumps(file_list)}
        pdata = urllib.urlencode( data )
        #print pdata
        conn = self._request( url, pdata )
        jdata = json.loads(conn.read())
        for f in jdata['info']:
            #print f
            try:
                print f['server_filename'],

                ltime=time.localtime(float(f['server_mtime']))
                timeStr=time.strftime("%Y-%m-%d %H:%M:%S", ltime)
                print timeStr,
                #print f['server_mtime']
                print sizeof_fmt( f['size'] ),

                print f['md5'],
                fid=f['fs_id']
                dlink=self.get_dlink(fid)
                if f['dlink'] != dlink:
                    f['dlink'] = dlink
                print f['dlink']
            except Exception, e:
                print e
                print jdata
        return jdata
    def get_dlink(self, fid):
        """
        get a fid download link, meta's dlink is dead.
        """
        fids='%5B'+str(fid)+'%5D'
        url = self.server + '/api/download?sign=%s&timestamp=%d&fidlist=%s&type=dlink&channel=chunlei&clienttype=0&web=1&app_id=250528&bdstoken=%s'% (self.user['sign'], self.user['timestamp'],fids, self.user['bdstoken'])
        #print url
        #print self.headers
        conn = self._request( url )
        jdata = json.loads(conn.read())
        '''{u'errno': 0, u'dlink': [{u'dlink': u'https://d.pcs.baidu.com/file/b4943a6b3e08e23c03fc2f6f0f28149a?fid=1964564887-250528-768969488&time=1471187673&rt=pr&sign=FDTAERVC-DCb740ccc5511e5e8fedcff06b081203-TMKjm%2FEOLfmZ72nps9QFfQNVoEM%3D&expires=8h&chkv=1&chkbd=1&chkpc=&dp-logid=5264038947921654203&dp-callid=0&r=978039963', u'fs_id': u'768969488'}], u'request_id': 5264038947921654203}
        '''
        try:
            return jdata['dlink'][0]['dlink']
        except Exception, e:
            #print e
            #print jdata
            return False

    def mk_aria2c_header(self):
        headers = ["Cookie: %s"% self.cookies,  "User-Agent: netdisk;5.3.4.5;PC;PC-Windows;5.1.2600;WindowsBaiduYunGuanJia", "Referer: http://pan.baidu.com/disk/home"]
        return headers

    def mk_aria2c(self, fpath, auth_url):
        # http://username:password@domain:6800/jsonrpc
        user_pass = auth_url.split('@')[0].split('//')[1]
        auth = base64.b64encode(user_pass).decode('utf-8')
        url  = auth_url.replace(user_pass+'@', '')

        jdata = self.meta(fpath)
        f = jdata['info'][0]
        dlink = f['dlink']
        name  = f['server_filename']
        rpc_data = {"jsonrpc": "2.0","method": "aria2.addUri", "id": int(time.time()),
                    "params": [ [dlink], {"out": name, "header": self.mk_aria2c_header()}]
                    };
        jsonreq = json.dumps(rpc_data)
        #print jsonreq
        req = urllib2.Request(url, data=jsonreq, headers={'Authorization': 'Basic %s'% auth})
        c = urllib2.urlopen(req)
        print c.read()


    def upload(self, file_path):
        pass

    def download(self, file_path, save_path):
        if save_path.startswith('http'):
            return self.mk_aria2c(file_path, save_path)

        jdata = self.meta( file_path )
        url = ''
        for f in jdata['info']:
            url = f['dlink']
            break
        if not url:
            print "Cannot found the dlink!"
            return False

        cmd = "wget -c --header 'Cookie: %s' --header 'User-Agent: netdisk;5.3.4.5;PC;PC-Windows;5.1.2600;WindowsBaiduYunGuanJia' '%s' -O '%s'"% (self.cookies, url, save_path)
        print cmd
        import os
        os.system(cmd)

    def dowload_dir(self, file_dir, save_dir):
        dir_list = self.list_file(file_dir)
        for f in dir_list['list']:
            if f['isdir'] == 1:
                continue
            print f
            if not save_path.startswith('http'):
                save_path=os.path.join(save_dir, f['server_filename'])
            self.download(f['path'], save_path)



if __name__ == "__main__":
    try:
        bd = BAIDU(sys.argv[1])
    except Exception, e:
        bd = BAIDU()

    if not bd.check_login():
        sys.exit(1)
    if not bd.check_sign():
        sys.exit(1)

    #print bd.user
    print bd.user['username'],
    bd.quota()
    bd.do()

