#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
libbbsarchiver.py

"""

# LOCAL
from config import database_init_statement

# GLOBAL
import re, sys, os
import sqlite3

def resetDatabase(filename='archive.db'):
    try:
        conn = sqlite3.connect(filename)
    except:
        raise
    c = conn.cursor()
    c.executescript(database_init_statement)
    conn.commit()
