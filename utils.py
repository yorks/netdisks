#!/usr/bin/env python2
#-*- coding: utf-8 -*-

import urllib2
import urllib
import os
import sys
import re
import getopt


import cookie_db

verbose=False



class PAN(object):
    def __init__(self, server, cookies=None):
        self.server = server
        self.cookies = cookies
        if not self.cookies:
            self._get_cookie()

        self.headers = {
            'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:18.0) Gecko/20100101 Firefox/18.0',
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer':self.server,
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
        cookies = cookie_db.get_cookie_from_db( '.baidu.com', ff_cookie_file_path, True)
        self.cookies = cookies
        if verbose:print "Got cookie from the firefox sqlit file."
        if verbose:print self.cookies

    def _request(self, url, data=None):
        if verbose: print "request url[%s]"% url
        if data:
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            self.headers['Content-Length'] = '%d'% len(data)
            if verbose:print self.headers, data
            req = urllib2.Request(url=url, data=data, headers=self.headers)
        else:
            if 'Content-Type' in self.headers:del self.headers['Content-Type']
            if 'Content-Length' in self.headers:del self.headers['Content-Length']
            if verbose:print self.headers
            req=urllib2.Request(url=url, headers=self.headers)

        conn = urllib2.urlopen(req)
        return conn

    def check_login(self):
        pass

    def list_file(self, path='/'):
        pass

    def list_offline_download(self):
        pass

    def add_offline_task(self, surl, save_path='/'):
        pass

    def meta(self, file_path):
        pass

    def upload(self, file_path):
        pass

    def download(self, file_path, save_path):
        pass

    def usage(self):
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

    def parse_input(self, c, cnt=2):
        re_str="""(ls|list|stat)\s+(["']{0,1}[^"']+["']{0,1})"""
        if cnt==3:
            re_str="""(get|g|m)\s+(["']{0,1}[^"']+["']{0,1})\s+(["']{0,1}[^"']+["']{0,1})"""
        what_arg = re.findall(re_str, c)
        if not what_arg:
            print "Input error"
            self.usage()
            return False
        return what_arg


    def _do(self, c):
        cmd = c.split()[0]
        if cmd in ['ls', 'list']:
            what_arg = self.parse_input(c)
            try:
                path = what_arg[0][1]
            except:
                return False
            self.list_file(path)

        elif cmd in ['stat']:
            what_arg = self.parse_input(c)
            try:
                path = what_arg[0][1]
            except Exception, e:
                return False
            self.meta(path)

        elif cmd in ['get']:
            what_arg = self.parse_input(c, 3)
            f_s = what_arg
            if not f_s:
                return False
            f = f_s[0][1].replace("'", '').replace('"','')
            s = f_s[0][2].replace("'", '').replace('"','')
            self.download(f, s)

        elif cmd in ['m']:
            what_arg = self.parse_input(c, 3)
            f_s = what_arg
            if not f_s:
                return False
            f = f_s[0][1].replace("'", '').replace('"','')
            s = f_s[0][2].replace("'", '').replace('"','')
            self.add_offline_task(f, s)

        elif cmd in ['offline', 'o']:
            self.list_offline_download()

        elif cmd in ['help', 'h']:
            self.usage()

        elif cmd in ['quit', 'q', 'exit']:
            sys.exit(1)
        else:
            print "Unkonw command!"
            self.usage()
            pass

    def do(self):
        while 1:
            c = raw_input('>>>')
            self._do( c )

# https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def parse_argv(command):
    try:
        opts, args = getopt.getopt(command, "d:c:p:f:l:vth", ["do=", "cookies=", "path=", "file=", "link=", "verbose", "test", "help"])
    except getopt.GetoptError, err:
        usage()
        sys.exit(1)

    do      = ''
    cookies = ''
    path    = ''
    lfile   = ''
    link    = ''
    verbose = False
    test    = False

    for o, v in opts:
        if o in ("-d", "--do"):
            do = v
        elif o in ("-c", "--cookies"):
            cookies = v
        elif o in ("-p", "--path"):
            path = v
        elif o in ("-f", "--file"):
            lfile = v
        elif o in ("-l", "--link"):
            link = v
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit(1)
        else:
            print "\033[1;31mError\033[m: Unkonw option!"
            usage()
            sys.exit(1)

    info={'do':do, 'cookies':cookies, 'path':path, 'lfile':lfile, 'link':link, 'verbose':verbose, 'test':test}
    return info



if __name__ == "__main__":
    arg = _parse_argv( sys.argv[1:] )
    if arg['do'] == '':
        pass
