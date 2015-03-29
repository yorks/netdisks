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
            self.user['uk'] = re.findall('yunData.MYUK = "(.*)";', html)[0]
            self.user['username'] = re.findall('yunData.MYNAME = "(.*)";', html)[0]
            self.user['bdstoken'] = re.findall('yunData.MYBDSTOKEN = "(.*)";', html)[0]
        except Exception, e:
            print e
            return False
        return self.user

    def list_file(self, path='/'):
        path = urllib.quote( path )
        url = self.server+'/api/list?channel=chunlei&clienttype=0&web=1&num=100&page=1&dir='+path+'&order=time&desc=1&showempty=0&_=1415186792830&bdstoken='+self.user['bdstoken']+'&channel=chunlei&clienttype=0&web=1&app_id=250528'

        conn = self._request( url )
        html = conn.read()
        foo = json.loads( html )
        for f in foo['list']:
            print f['path']

    def list_offline_download(self):
        url = self.server + '/rest/2.0/services/cloud_dl?bdstoken='+self.user['bdstoken']+'&need_task_info=1&status=255&start=0&limit=10&method=list_task&app_id=250528&t=1415191187214&channel=chunlei&clienttype=0&web=1'
        conn = self._request( url )
        html = conn.read()
        foo = json.loads( html )
        for t in foo['task_info']:
            print t['task_name'], t['status']

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

    def meta(self, file_path):
        file_list = []
        file_list.append( file_path )
        url = self.server + '/api/filemetas?blocks=0&dlink=1&method=filemetas&channel=chunlei&clienttype=0&web=1&app_id=250528&bdstoken='+self.user['bdstoken']
        data = {'target':json.dumps(file_list)}
        pdata = urllib.urlencode( data )
        conn = self._request( url, pdata )
        jdata = json.loads(conn.read())
        for f in jdata['info']:
            try:
                print f['server_filename'],

                ltime=time.localtime(float(f['server_mtime']))
                timeStr=time.strftime("%Y-%m-%d %H:%M:%S", ltime)
                print timeStr,
                #print f['server_mtime']
                print sizeof_fmt( f['size'] ),

                print f['md5']
                print f['dlink']
            except Exception, e:
                print e
                print jdata
        return jdata

    def upload(self, file_path):
        pass

    def download(self, file_path, save_path):
        jdata = self.meta( file_path )
        url = ''
        for f in jdata['info']:
            url = f['dlink']
            break
        if not url:
            print "Cannot found the dlink!"
            return False

        cmd = "wget -c --header 'Cookie: %s' --header 'User-Agent: netdisk;3.9.0.2;PC;PC-Windows;5.1.2600;WindowsBaiduYunTongBuPan' '%s' -O '%s'"% (self.cookies, url, save_path)
        print cmd
        import os
        os.system(cmd)

if __name__ == "__main__":
    try:
        bd = BAIDU(sys.argv[1])
    except Exception, e:
        bd = BAIDU()

    if not bd.check_login():
        sys.exit(1)
    print bd.user['username']
    bd.do()

