#!/usr/bin/env python3

import os
import sys
import sqlite3
import html
import bs4
import requests
import urllib

"""
configuration status.
"""
target_board = "Linux"
board_size = 24000
running_status = "default"
database_init_statement="""
        BEGIN EXCLUSIVE TRANSACTION;
        DROP TABLE IF EXISTS `linux`;
        DROP TABLE IF EXISTS `boards`;
        CREATE TABLE `boards` (
            `name` TEXT NOT NULL,
            `cname` TEXT NOT NULL,
            `postnumber` INTEGER NOT NULL,
            `finalpost` INTEGER NOT NULL
        );
        END TRANSACTION;
        """
