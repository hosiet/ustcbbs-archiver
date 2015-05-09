#!/usr/bin/env python3

import os
import sys
import sqlite3
import bs4
import requests

"""
configuration status.
"""
target_board = "Linux"
board_size = 24000
running_status = "default"
database_init_statement="""
        BEGIN EXCLUSIVE TRANSACTION;
        CREATE TABLE IF NOT EXISTS `boards` (
            `name` TEXT NOT NULL,
            `cname` TEXT NOT NULL,
            `postnumber` INTEGER NOT NULL,
            `finalpost` INTEGER NOT NULL
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
            `re` INTEGER NOT NULL,
            `thread` INTEGER NOT NULL,
            `text` TEXT
        );
        END TRANSACTION;
        """
