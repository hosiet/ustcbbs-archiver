#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
download.py

"""

# LOCAL
from bbsarchiver.config import database_init_statement
from bbsarchiver.Database import *
from bbsarchiver.libbbsarchiver import *

# GLOBAL
import sys, os, argparse, time

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--no-update-list", help="don't update any board post list.", action="store_true");
    parser.add_argument("-i", "--init-database", help="clean database and reconstruct(DANGEROUS!)", action="store_true")
    parser.add_argument("-o", "--output", help="specify output file.", default="archive.db")
    parser.add_argument("-b", "--board", help="specify download board info.")
    args = parser.parse_args()
    filepath = args.output
    if args.no_update_list:
        print("FLAG: WONT update list.")
        onlytext_flag = True
    else:
        print("FLAG: WILL update list.")
        onlytext_flag = False
    if args.init_database:
        print("FLAG: WILL update db.")
        init_flag = True
    else:
        print("FLAG: WONT update db.")
        init_flag = False

    time.sleep(2)
    conn = initSQLiteConn(filename=filepath, initialize=init_flag)
    updateBoardAll(args.board, conn, onlytext=onlytext_flag)
    sys.exit(0)

else:
    pass
