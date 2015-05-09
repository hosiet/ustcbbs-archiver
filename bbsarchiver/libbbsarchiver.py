#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
libbbsarchiver.py

"""

# LOCAL
from bbsarchiver.config import *
from bbsarchiver.Database import *

# GLOBAL
import requests, re, sys, os, sqlite3, time, argparse
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

def initSQLiteConn(boardname, filename='archive.db', initialize=False):
    try:
        conn = sqlite3.connect(filename)
    except:
        raise
    if initialize == True:
        # initialize database
        c = conn.cursor()
        c.executescript(database_init_statement)
        c.executescript(database_init_board_statement.format(boardname))

    return conn

# #######  SOUP metadata_retrieve func

def updateBoardInfo(boardname, url, conn, auth, partial=False, startwith=1):
    """
    更新版面信息。

    partial: 不从头进行筛查，仅根据原有个数筛查（不推荐）
    """
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

    # 确定更新上限
    max_boardpost = int(i)
    repeat_top = (max_boardpost // 20 * 20) + 20 - (max_boardpost - ((max_boardpost // 20) * 20))
    print('DEBUG: repeat_top would be {0}'.format(repeat_top), file=sys.stderr)

    lowstart = 1
    # 确定更新下限
    ## TODO FIXME DETERMINE CORRECT TIME!!!
    ## TODO DELETE ME
    if partial == True:
        c = conn.cursor()
        for maxcount in c.execute('SELECT COUNT(`time`) FROM {0};'.format(boardname)):
                print('DEBUG: total {0}.'.format(maxcount[0]))
                if maxcount[0] == 0:
                    maxcount[0] = 1
                break

    ## 确定更新下限
    if lowstart == 1:
        lowstart = startwith

    for startpage in range(lowstart, repeat_top, 20):
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
            current_status = i.find_all('td')[1].string[0]
            hrefstring = i.find_all('td')[6].find_all('a')[1].attrs['href'].split('&')[1][3:]
            current_type = hrefstring[0]
            current_time = int(hrefstring[1:], 16)
            try:
                tmpstr = i.find_all('td')[2].a.string
            except AttributeError:
                tmpstr = i.find_all('td')[2].string
            current_title = i.find_all('td')[6].find_all('a')[1].string
            if i.find_all('td')[6].find_all('a')[0].string == 'Re: ':
                current_re = 1
            else:
                current_re = 0
            current_thread_time = i.find_all('td')[6].a.attrs['href'].split('&')[1].split('.')[1]
            bypass_this = False
            for tmpresult in c.execute('SELECT `time` FROM {0} WHERE `time` = ?;'.format(boardname), (current_time,)):
                bypass_this = True
                break
            if bypass_this == False:
                c.execute('INSERT INTO {0} VALUES(?, ?, ?, ?, ?, ?, null);'.format(boardname), (current_time, current_type, current_status, current_title, current_re, current_thread_time));
            bypass_this = False

def updateBoardPostOnce(boardname, url, conn, auth):
    """
    insert board info 

    更新文章内容
    Note: url shall be from bbscon: http://bbs.ustc.edu.cn/cgi/bbscon?bn={0}&fn=XXX[&num=XXX]
    """
    post_link = url.split('?')[1].split('&')[1].split('=')[1]
    print('debug: post_link is {0}'.format(post_link), end="")
    resp = getURLResponse(url)
    soup = BeautifulSoup(resp.text)
    for post_text in soup.find_all('div'):
        if 'class' in post_text.attrs.keys() and post_text.attrs['class'] == ['post_text']:
            current_text = post_text.prettify(formatter="html")
            #print('DEBUG:current_text is {0}'.format(current_text))
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


def updateBoardAll(boardname, conn, auth=None, onlytext=False, startwith=1):
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
        updateBoardInfo(boardname, url="http://bbs.ustc.edu.cn/cgi/bbsdoc?board={0}&start={1}", conn=conn, auth=auth, startwith=startwith)

    # Update post data
    updateBoardPost(boardname, url="http://bbs.ustc.edu.cn/cgi/bbscon?bn={bname}&fn={number}", conn=conn, auth=auth)

    print("All Done.")
    return True


# #################################################


if __name__ == '__main__':
    pass
else:
    pass
