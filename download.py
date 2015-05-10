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
    parser.add_argument("-b", "--board", help="specify download board info.", required=True)
    parser.add_argument("-s", "--start-with", help="specify the beginning of updateBoardInfo().")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug verbose.")
    args = parser.parse_args()
    filepath = args.output
    startwith = int(args.start_with)
    if args.verbose:
        debug_output = True
    else:
        debug_output = False
    printCopyrightInfo()
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

    print('ready...', end='', flush=True)
    time.sleep(1)
    print('3,2,1...', end='', flush=True)
    time.sleep(1)
    print('Go!')
    conn = initSQLiteConn(args.board, filename=filepath, initialize=init_flag)
    updateBoardAll(args.board, conn, onlytext=onlytext_flag, startwith=startwith)
    sys.exit(0)

else:
    pass
