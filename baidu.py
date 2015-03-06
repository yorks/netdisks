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

verbose=False


class BAIDU(object):
    def __init__(self, cookies=None):
        self.server = 'http://pan.baidu.com'
        self.cookies = cookies
        if not self.cookies:
            self._get_cookie()

        self.headers = {
            'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:18.0) Gecko/20100101 Firefox/18.0',
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer':'http://pan.baidu.com/disk/home',
            'Cookie':'%s'% self.cookies
            }

        self.user = {}
        self.offline_status = {'1':'downloading', '0':'done'}

    def _get_cookie(self):
        cookies=''
        ff_cookie_file_path = cookie_db.get_firefox_cookie_file()
        if not ff_cookie_file_path:
            ff_cookie_file_path = raw_input('cannot found firefox cookie file, pls input its abs path:')
            if os.path.isfile( ff_cookie_file_path ):
                print "Input error, you iput the file not exist or not a file!"
                sys.exit(1)
        baidu_cookies = cookie_db.get_cookie_from_db(ff_cookie_file_path, '.baidu.com')
        baidu_pan_cookies = cookie_db.get_cookie_from_db(ff_cookie_file_path, 'pan.baidu.com')
        cookies = baidu_cookies + baidu_pan_cookies
        self.cookies = cookies
        print "Got cookie from the firefox sqlit file."
        print self.cookies

    def _request(self, url, data=None):
        if verbose: print "request url[%s]"% url
        if data:
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            self.headers['Content-Length'] = '%d'% len(data)
            req = urllib2.Request(url=url, data=data, headers=self.headers)
        else:
            if 'Content-Type' in self.headers:del self.headers['Content-Type']
            if 'Content-Length' in self.headers:del self.headers['Content-Length']
            req=urllib2.Request(url=url, headers=self.headers)

        conn = urllib2.urlopen(req)
        return conn

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
        url = self.server + '/api/list?channel=chunlei&clienttype=0&web=1&num=100&page=1&dir='+path+'&order=time&desc=1&showempty=0&_=1415186792830&bdstoken='+self.user['bdstoken']+'&channel=chunlei&clienttype=0&web=1&app_id=250528'
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

    def meta(self, file_list):
        url = self.server + '/api/filemetas?blocks=0&dlink=1&method=filemetas&channel=chunlei&clienttype=0&web=1&app_id=250528&bdstoken='+self.user['bdstoken']
        data = {'target':json.dumps(file_list)}
        pdata = urllib.urlencode( data )
        conn = self._request( url, pdata )
        jdata = json.loads(conn.read())
        for f in jdata['info']:
            try:
                print f['server_filename']

                ltime=time.localtime(float(f['server_mtime']))
                timeStr=time.strftime("%Y-%m-%d %H:%M:%S", ltime)
                print timeStr
                #print f['server_mtime']
                print f['size'] / 1024 / 1024, "MB"

                print f['md5']
                print f['dlink']
            except Exception, e:
                print e
                print jdata
        return jdata

    def upload(self, file_path):
        pass

    def download(self, file_path, save_path):
        file_list = [ file_path ]
        jdata = self.meta( file_list )
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

def usage():
    msg = '''
    ===============Please follow the belove Command==================
    -------------- 'ls /path'   for list file&dir  ------------------
    -------------- 'stat /path' for stat the file info(md5, dlink...)
    -------------- 'get /path /savepath' for download the file ......
    -------------- 'offline'    for see the offline tasklist --------
    -------------- 'm murl /savepath' add magnet download tasklist --
    -------------- 'q'          for quit this program      ----------
    -------------- 'h'          for Help (this HelpMessage)----------
    '''
    print msg

def do(c, pan):
    if c.startswith('ls '):
        d = c.replace('ls ', '')
        pan.list_file(d)

    elif c.startswith('stat '):
        f = c.replace('stat ', '')
        flist = [ f ]
        pan.meta(flist)
    elif c == 'offline':
        pan.list_offline_download()
    elif c.startswith('m '):
        surl = c.split()[1]
        sd  = c.split()[2]
        pan.add_offline_task(surl, sd)
    elif c.startswith('get '):
        f_s = re.findall("""get\s+(["']{0,1}[^"']+["']{0,1})\s+(["']{0,1}[^"']+["']{0,1})""", c)
        if not f_s:
            print "input error, %s"% c
            usage()
            return
        f = f_s[0][0].replace("'", '').replace('"','')
        s = f_s[0][1].replace("'", '').replace('"','')

        #f  = c.split()[1]
        #s  = c.split()[2]
        pan.download(f, s)

    elif c == 'q':
        sys.exit(1)
    else:
        print "Unkonw command!"
        usage()

if __name__ == "__main__":
    try:
        bd = BAIDU(sys.argv[1])
    except Exception, e:
        bd = BAIDU()

    if not bd.check_login():
        sys.exit(1)
    print bd.user['username']
    while True:
        c=raw_input('>>>')
        do(c, bd)

