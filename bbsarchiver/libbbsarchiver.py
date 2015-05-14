#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
libbbsarchiver.py

"""

# LOCAL
from .config import *
from .Database import *

# GLOBAL
import requests, re, sys, os, sqlite3, time, argparse
from bs4 import BeautifulSoup
from html.parser import HTMLParser
import time

def printCopyrightInfo():
    print("USTCBBS Archiver v0.1 [dev]")
    print("Copyright (c) 2015 Boyuan Yang <073plan@gmail.com>")
    print("All Rights Reserved.\n", flush=True)

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

def debugOutput(text, level='Debug', force=False, ret=False):
    """
    Show debug info.
    """
    if ret == True:
        endstring = '\n'
    else:
        endstring = ''

    try:
        result = debug_output
    except NameError:
        debug_output = False
    if force == True or debug_output == True:
        print('{1}[{0}]'.format(level.upper(), endstring), text, end='\n', sep=' ', flush=True, file=sys.stderr)

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
        debugOutput('database init statement called.')
        c.executescript(database_init_board_statement.format(boardname))
        debugOutput('board {0} init statement called.'.format(boardname))

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
    debugOutput('repeat_top is {0}'.format(repeat_top))
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
        print('\rupdating board info: {0} / {1} ...'.format(startpage, repeat_top), end='')
        conn.commit()
    print('')


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
    c = conn.cursor()
    #c.execute('INSERT INTO `boards` VALUES(?, ?, ?, ?)', ('linux', 'dd', i, 0))
    #conn.commit()
    for i in soup.find_all('tr'):
        if 'class' in i.attrs.keys() and (i.attrs['class'] == ['M'] or i.attrs['class'] == ['new'] or i.attrs['class'] == ['G']):
            current_status = i.find_all('td')[1].string[0]
            hrefstring = i.find_all('td')[6].find_all('a')[1].attrs['href'].split('&')[1][3:]
            current_type = hrefstring[0]
            current_time = int(hrefstring[1:], 16)
            try:
                current_author = i.find_all('td')[2].a.string
            except AttributeError:
                current_author = i.find_all('td')[2].string
            if current_author == None:
                debugOutput('current_author is None (parsing error)', level='Warn', force=True)
            current_title = i.find_all('td')[6].find_all('a')[1].string
            if i.find_all('td')[6].find_all('a')[0].string == 'Re: ':
                current_re = 1
            else:
                current_re = 0
            current_thread_time = i.find_all('td')[6].a.attrs['href'].split('&')[1].split('.')[1]
            bypass_this = False
            for tmpresult in c.execute('SELECT `time` FROM {0} WHERE `time` = ?;'.format(boardname), (current_time,)):
                debugOutput('post {0} in board {1} has been logged already, skipping...'.format(current_time, boardname))
                bypass_this = True
                break
            if bypass_this == False:
                c.execute('INSERT INTO {0} VALUES(?, ?, ?, ?, ?, ?, ?, null);'.format(boardname), (current_time, current_type, current_status, current_title, current_author, current_re, current_thread_time));
            bypass_this = False

def updateBoardPostOnce(boardname, url, conn, auth):
    """
    insert board info 

    更新文章内容
    Note: url shall be from bbscon: http://bbs.ustc.edu.cn/cgi/bbscon?bn={0}&fn=XXX[&num=XXX]
    """
    post_link = url.split('?')[1].split('&')[1].split('=')[1]
    debugOutput('processing post_link {0}..'.format(post_link))
    resp = getURLResponse(url)
    soup = BeautifulSoup(resp.text)
    c = conn.cursor()
    print('\rProcessing post {0} ...'.format(post_link), end='')
    for post_text in soup.find_all('div'):
        if 'class' in post_text.attrs.keys() and post_text.attrs['class'] == ['post_text']:
            current_text = post_text.prettify(formatter="html")
            #print('DEBUG:current_text is {0}'.format(current_text))
            # something
            # FIXME on error do STH
            c.execute('UPDATE {0} SET `text` = ? WHERE `time` = ?'.format(boardname), (current_text, int(post_link[1:], 16)))
            conn.commit()
            break


def updateBoardPost(boardname, url, conn, auth):
    c = conn.cursor()
    for emptypostnum in c.execute('SELECT COUNT(*) FROM {0} WHERE `text` IS NULL'.format(boardname)):
        print('{0} posts left to be done.'.format(emptypostnum[0]))
    for posttimelist in c.execute('SELECT `time` FROM {0} WHERE `text` is null ORDER BY `time` ASC;'.format(boardname)):
        posttime_hex = hex(posttimelist[0])[2:].upper()
        nexturl = url.format(bname=boardname, number=('M'+posttime_hex))
        updateBoardPostOnce(boardname, nexturl, conn, auth)
    print('')

def updateBoardTable(boardname, conn):
    """
    Update Statistic for current board.

    Write into `boards` table in the database.
    """
    current_cname = BeautifulSoup(requests.get(url_bbsdoc.format(boardname, 1)).text).title.string.split('[')[1].split(']')[0]
    c = conn.cursor()
    for i in c.execute('SELECT COUNT(*) FROM {0};'.format(boardname)):
        break
    if i == None:
        raise Exception('SQL Query Failed in updateBoardTable()!')
    current_postnumber = i[0]
    i = None
    for i in c.execute('SELECT MAX(`time`) FROM {0};'.format(boardname)):
        break
    if i == None:
        raise Exception('SQL Query Failed in updateBoardTable()!')
    current_finalpost = i[0]
    i = None
    for i in c.execute('SELECT `name` FROM `boards` WHERE `name` IS ?', (boardname,)):
        break
    if i == None:
        debugOutput('No similar board record found. Will add one.')
        c.execute('INSERT INTO `boards` (`name`, `cname`, `postnumber`, `finalpost`) VALUES(?, ?, ?, ?);', (boardname, current_cname, current_postnumber, current_finalpost))
    else:
        debugOutput('Similar board record found. Updating data.')
        c.execute('UPDATE `boards` SET `postnumber`=?, `finalpost`=? WHERE `name` IS \'{0}\';'.format(boardname), (current_postnumber, current_finalpost))
    conn.commit()

def printBoardStatistic(boardname, conn):
    """
    Print Statistic for current board.
    """
    c = conn.cursor()
    for i in c.execute('SELECT * FROM `boards` WHERE `name` IS ?', (boardname,)):
        break
    if i == None:
        raise Exception('SQL Query Failed! in printBoardStatistic()')
    print('name: {0}\ncname: {1}\narchived_posts: {2}\nlatest_post: {3}\nlatest_post_time: {4}'.format(i[0], i[1], i[2], i[3], time.strftime("%a, %d %b %Y %H:%M:%S %z", time.localtime(i[3]))))
    return

def updateBoardAll(boardname, conn, auth=None, onlytext=False, startwith=1):
    """
    update All board-related info in SQLite3 connection `conn`.

    Will use given url to retrieve data.

    Steps are as follows:

    *  Update all post info and do not download them.
    *  Download all new posts and save them into the database.
    """
    # FIXME auth support

    boardname = boardname.lower()
    try:
        # Update post info
        if onlytext == False:
            print('[Step 1] update board list...')
            updateBoardInfo(boardname, url=url_bbsdoc, conn=conn, auth=auth, startwith=startwith)
            print('')

        # Update post data
        print('[Step 2] update board text...')
        updateBoardPost(boardname, url=url_bbscon, conn=conn, auth=auth)
    except:
        debugOutput('An Exception was caught.', force=True, level='Error', ret=True)
        raise
    finally:
        print('[Step 3] update boards table...')
        updateBoardTable(boardname, conn)
        printBoardStatistic(boardname, conn)
        conn.commit()

    print("\nAll Done.")
    return True


# #################################################


if __name__ == '__main__':
    pass
else:
    pass
