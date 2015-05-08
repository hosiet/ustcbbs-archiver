#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
libbbsarchiver.py

"""

# LOCAL
from bbsarchiver.config import database_init_statement
from bbsarchiver.Database import *

# GLOBAL
import requests, urllib, re, sys, os, sqlite3, time, argparse
from bs4 import BeautifulSoup
from html.parser import HTMLParser

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
    # for debug
    print('DEBUG: repeat_top would be {0}'.format(repeat_top))

    #c = conn.cursor()
    #c.execute('CREATE TABLE {0} (`time` INTEGER NOT NULL, `type` CHAR(1) NOT NULL, `title` TEXT NOT NULL, `re` INTEGER NOT NULL, `thread` INTEGER NOT NULL, `text` TEXT)'.format(boardname))
    for startpage in range(1, repeat_top, 20):
        updateBoardInfoOnce(boardname, url, conn, auth, startpage)
        sys.stderr.write('finished startpage {0}.\n'.format(startpage))
        sys.stderr.write('Sleeping for 1 sec...\n')
        #time.sleep(1)
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
            #print('number:', int(i.find_all('td')[0].string))
            current_status = i.find_all('td')[1].string
            #print('status:', current_status)
            hrefstring = i.find_all('td')[6].find_all('a')[1].attrs['href'].split('&')[1][3:]
            #print(hrefstring)
            current_type = hrefstring[0]
            #print('articletype:{0}'.format(hrefstring[0]))
            #print('link:{0}'.format(hrefstring))
            current_time = int(hrefstring[1:], 16)
            #print('time:{0}'.format(current_time))
            try:
                tmpstr = i.find_all('td')[2].a.string
            except AttributeError:
                tmpstr = i.find_all('td')[2].string
            #print('author:', tmpstr)
            current_title = i.find_all('td')[6].find_all('a')[1].string
            #print('title:', i.find_all('td')[6].find_all('a')[0].string, current_title)
            #print('is_Re:', end='')
            if i.find_all('td')[6].find_all('a')[0].string == 'Re: ':
                current_re = 1
                #print('yes')
            else:
                current_re = 0
                #print('no')
            current_thread_time = i.find_all('td')[6].a.attrs['href'].split('&')[1].split('.')[1]
            #print('thread_time:{0}'.format(current_thread_time))
            #print('thread_link:{0}'.format('M'+hex(int(current_thread_time))[2:].upper()))
            #print('--------------')
            bypass_this = False
            for tmpresult in c.execute('SELECT `time` FROM {0} WHERE `time` = ?;'.format(boardname), (current_time,)):
                bypass_this = True
                break
            if bypass_this == False:
                c.execute('INSERT INTO {0} VALUES(?, ?, ?, ?, ?, null);'.format(boardname), (current_time, current_type, current_title, current_re, current_thread_time));
            bypass_this = False

def updateBoardPostOnce(boardname, url, conn, auth):
    """
    insert board info 

    Note: url shall be from bbscon: http://bbs.ustc.edu.cn/cgi/bbscon?bn={0}&fn=XXX[&num=XXX]
    """
    post_link = url.split('?')[1].split('&')[1].split('=')[1]
    print('debug: post_link is {0}'.format(post_link), end="")
    resp = getURLResponse(url)
    soup = BeautifulSoup(resp.text)
    for post_text in soup.find_all('div'):
        if 'class' in post_text.attrs.keys() and post_text.attrs['class'] == ['post_text']:
            current_text = post_text.__str__()
            #print('current_text is {0}'.format(current_text))
            # something
            # FIXME on error do STH
            c = conn.cursor()
            c.execute('UPDATE {0} SET `text` = ? WHERE `time` = ?'.format(boardname), (current_text, int(post_link[1:], 16)))
            conn.commit()
            break
    print("...done!")


def updateBoardPost(boardname, url, conn, auth):
    c = conn.cursor()
    for posttimelist in c.execute('SELECT `time` FROM {0} WHERE `text` is null ORDER BY `time` ASC;'.format(boardname)):
        posttime_hex = hex(posttimelist[0])[2:].upper()
        nexturl = url.format(bname=boardname, number=('M'+posttime_hex))
        updateBoardPostOnce(boardname, nexturl, conn, auth)


def updateBoardAll(boardname, conn, auth=None, onlytext=False):
    """
    update All board-related info in SQLite3 connection `conn`.

    Will use given url to retrieve data.

    Steps are as follows:

    *  Update all post info and do not download them.
    *  Download all new posts and save them into the database.
    """
    # FIXME auth support

    # Update post info
    if onlytext == False:
        updateBoardInfo(boardname, url="http://bbs.ustc.edu.cn/cgi/bbsdoc?board={0}&start={1}", conn=conn, auth=auth)

    # Update post data
    updateBoardPost(boardname, url="http://bbs.ustc.edu.cn/cgi/bbscon?bn={bname}&fn={number}", conn=conn, auth=auth)

    print("All Done.")
    return True


# #################################################


if __name__ == '__main__':
    pass
else:
    pass
