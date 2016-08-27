#!/usr/bin/env python2
#-*- code: utf-8 -*-

import os
import sys
try:
    import sqlite3
except:
    print "sqlit3 module not found"
    sqlite3=None

def get_firefox_cookie_file():
    firefox_dir=os.path.expanduser('~/.mozilla/firefox/')
    cookie_file_path=''
    try:
        dir_list = os.listdir(firefox_dir)
        for d in dir_list:
            cookie_dir=os.path.join(firefox_dir,d)
            if os.path.isdir(cookie_dir) and d.endswith('default'):
                cookie_file_path=os.path.join(cookie_dir,'cookies.sqlite')
                if not os.path.isfile(cookie_file_path):
                    raise "cookie file not exist!"
                break
            else:
                continue
    except:
        return False
    if not cookie_file_path:
        return False
    return cookie_file_path

def get_cookie_from_db(host, cookie_db_file=None, like=False):
    cookies=''
    if not cookie_db_file:
        cookie_db_file = get_firefox_cookie_file()
    sql_cmd="select name,value from moz_cookies where host = '%s';"% host
    if like:
        sql_cmd="select name,value from moz_cookies where host like '%%%s';"% host
    if sqlite3 is None:
        return ''
    conn = sqlite3.connect(cookie_db_file)
    c = conn.cursor()

    """
    # one row
    (0, u'id', u'INTEGER', 0, None, 1)
    (1, u'name', u'TEXT', 0, None, 0)
    (2, u'value', u'TEXT', 0, None, 0)
    (3, u'host', u'TEXT', 0, None, 0)
    (4, u'path', u'TEXT', 0, None, 0)
    (5, u'expiry', u'INTEGER', 0, None, 0)
    (6, u'lastAccessed', u'INTEGER', 0, None, 0)
    (7, u'isSecure', u'INTEGER', 0, None, 0)
    (8, u'isHttpOnly', u'INTEGER', 0, None, 0)
    (9, u'baseDomain', u'TEXT', 0, None, 0)
    (10, u'creationTime', u'INTEGER', 0, None, 0)
    """
    for row in c.execute(sql_cmd):
        cookies=cookies+row[0]+'='+row[1]+'; '
    return cookies


if __name__ == "__main__":
    cookies = get_cookie_from_db('.baidu.com')
    cookies = get_cookie_from_db('.baidu.com', None, True)
    print cookies
