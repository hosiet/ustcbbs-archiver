#!/usr/bin/env python3

import os, sys, re, requests, sqlite3

"""
configuration status.
"""
target_board = "Linux"
board_size = 24000
#debug_output = False
running_status = "default"
url_bbsdoc = "http://bbs.ustc.edu.cn/cgi/bbsdoc?board={0}&start={1}"
url_bbscon = "http://bbs.ustc.edu.cn/cgi/bbscon?bn={bname}&fn={number}"
database_init_statement="""
        BEGIN EXCLUSIVE TRANSACTION;
        CREATE TABLE IF NOT EXISTS `boards` (
            `name` TEXT NOT NULL,
            `cname` TEXT NOT NULL,
            `postnumber` INTEGER NOT NULL,
            `finalpost` INTEGER
        );
        END TRANSACTION;
        """
database_init_board_statement="""
        BEGIN EXCLUSIVE TRANSACTION;
        CREATE TABLE IF NOT EXISTS `{0}` (
            `time` INTEGER NOT NULL,
            `type` CHAR(1) NOT NULL,
            `status` CHAR(1) NOT NULL,
            `title` TEXT NOT NULL,
            `author` TEXT,
            `re` INTEGER NOT NULL,
            `thread` INTEGER NOT NULL,
            `text` TEXT
        );
        END TRANSACTION;
        """
