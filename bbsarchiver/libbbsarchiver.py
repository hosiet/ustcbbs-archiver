#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
libbbsarchiver.py

"""

# LOCAL
from config import database_init_statement
from Database import *

# GLOBAL
import requests
import urllib
import re, sys
from bs4 import BeautifulSoup
from html.parser import HTMLParser
import sqlite3
import time

def getURLResponse(url):
    """
    get response by requests.get .
    """
    try:
        response = requests.get(url)
    except:
        raise
    if response.status_code != 200:
        raise
    # TODO Test for validity. e.g. bad request or something.
    return response

# ######### SQLite3 Functions #####################

def initSQLiteConn(filename='archive.db', initialize=False):
    try:
        conn = sqlite3.connect(filename)
    except:
        raise
    if initialize == True:
        # initialize database
        c = conn.cursor()
        c.executescript(database_init_statement)

    return conn

# #######  SOUP metadata_retrieve func

def updateBoardInfo(boardname, url, conn, auth):
    resp = getURLResponse(url.format(boardname, 1))
    soup = BeautifulSoup(resp.text)
    # 得到当前文章总数
    mlist = re.findall('[0-9]*', soup.div.find_all('span')[3].string)
    for i in mlist:
        if i != None and i != '':
            break
    if i == None:
        raise Exception('No metadata found.')
        sys.exit(-1)
    max_boardpost = int(i)
    repeat_top = (max_boardpost // 20 * 20) + 20 - (max_boardpost - ((max_boardpost // 20) * 20))
    print('DEBUG: repeat_top would be {0}'.format(repeat_top))

    c = conn.cursor()
    c.execute('CREATE TABLE {0} (`time` INTEGER NOT NULL, `type` CHAR(1) NOT NULL, `title` TEXT NOT NULL, `re` INTEGER NOT NULL, `thread` INTEGER NOT NULL, `text` TEXT)'.format(boardname))
    for startpage in range(1, repeat_top, 20):
        updateBoardInfoOnce(boardname, url, conn, auth, startpage)
        sys.stderr.write('finished startpage {0}.\n'.format(startpage))
        sys.stderr.write('Sleeping for 1 sec...\n')
        time.sleep(1)
        conn.commit()


def updateBoardInfoOnce(boardname, url, conn, auth, startpage):
    """
    update Board Info once from given url and start_number

    Use SQLite3.
    """
    resp = getURLResponse(url.format(boardname, startpage))
    soup = BeautifulSoup(resp.text)
    # 得到当前文章总数
    mlist = re.findall('[0-9]*', soup.div.find_all('span')[3].string)
    for i in mlist:
        if i != None and i != '':
            break
    if i == None:
        raise Exception('No metadata found.')
        sys.exit(-1)
    print('当前文章总数：{0}'.format(i))
    c = conn.cursor()
    #c.execute('INSERT INTO `boards` VALUES(?, ?, ?, ?)', ('linux', 'dd', i, 0))
    #conn.commit()
    for i in soup.find_all('tr'):
        if 'class' in i.attrs.keys() and (i.attrs['class'] == ['M'] or i.attrs['class'] == ['new']):
            print('number:', int(i.find_all('td')[0].string))
            current_status = i.find_all('td')[1].string
            print('status:', current_status)
            hrefstring = i.find_all('td')[6].find_all('a')[1].attrs['href'].split('&')[1][3:]
            print(hrefstring)
            current_type = hrefstring[0]
            print('articletype:{0}'.format(hrefstring[0]))
            print('link:{0}'.format(hrefstring))
            current_time = int(hrefstring[1:], 16)
            print('time:{0}'.format(current_time))
            try:
                tmpstr = i.find_all('td')[2].a.string
            except AttributeError:
                tmpstr = i.find_all('td')[2].string
            print('author:', tmpstr)
            current_title = i.find_all('td')[6].find_all('a')[1].string
            print('title:', i.find_all('td')[6].find_all('a')[0].string, current_title)
            print('is_Re:', end='')
            if i.find_all('td')[6].find_all('a')[0].string == 'Re: ':
                current_re = 1
                print('yes')
            else:
                current_re = 0
                print('no')
            current_thread_time = i.find_all('td')[6].a.attrs['href'].split('&')[1].split('.')[1]
            print('thread_time:{0}'.format(current_thread_time))
            print('thread_link:{0}'.format('M'+hex(int(current_thread_time))[2:].upper()))
            print('--------------')
            c.execute('INSERT INTO {0} VALUES(?, ?, ?, ?, ?, null);'.format(boardname), (current_time, current_type, current_title, current_re, current_thread_time));

def updateBoardPost(boardname, url, conn, auth):
    pass

def updateBoardAll(boardname, conn, url="http://bbs.ustc.edu.cn/cgi/bbsdoc?board={0}&start={1}", auth=None):
    """
    update All board-related info in SQLite3 connection `conn`.

    Will use given url to retrieve data.

    Steps are as follows:

    *  Update all post info and do not download them.
    *  Download all new posts and save them into the database.
    """
    # FIXME auth support

    # Update post info
    updateBoardInfo(boardname, url, conn, auth)

    # Update post data
    updateBoardPost(boardname, url, conn, auth)

    print("All Done.")
    return True


# #################################################


if __name__ == '__main__':
    conn = initSQLiteConn(filename='archive.db', initialize=True)
    updateBoardAll('Linux', conn)

    sys.exit(0)
    # get text

    response = getURLResponse('http://bbs.ustc.edu.cn/cgi/bbsdoc?board=Linux')
    #print(response.text)

    # parse with BS4
    soup = BeautifulSoup(response.text)

    # get metadata
    infotag = soup.div
    tmptag = infotag.find_all('span')[3]
    tstring = tmptag.string
    mlist = re.findall('[0-9]*', tstring)
    for i in mlist:
        if i != None and i != '':
            break
    if i == None:
        raise Exception('No metadata found.')
        sys.exit(-1)
    print(i)

    # process current standard articles
    #initSQLiteConn('a.db', True)
    # tr class=new
    
else:
    pass
