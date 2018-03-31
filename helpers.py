import csv
import urllib.request

from flask import redirect, render_template, request, session
from functools import wraps

import pymysql
import pymysql.cursors


# AWS DB
host = "alumnidb.cokfw1k7ijz0.us-east-2.rds.amazonaws.com"
port = 3306
dbname = "innodb"
user = "sasharamani"
password = "Freedom55!?"


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def phoneProvided():
    query = "SELECT phone FROM innodb.alumni WHERE id = %(id)s"
    params = {}
    params['id'] = session.get("user_id")

    db = rundbquery(query, params)
    for row in db:
        if row[0] == 0 or row[0] == "" or row[0] is None:
            return 0
        else:
            return 1


def linkedinProvided():
    query = "SELECT linkedin FROM innodb.alumni WHERE id = %(id)s"
    params = {}
    params['id'] = session.get("user_id")

    db = rundbquery(query, params)
    for row in db:
        if row[0] == 0 or row[0] == "" or row[0] is None:
            return 0
        else:
            return 1


def facebookProvided():
    query = "SELECT facebook FROM innodb.alumni WHERE id = %(id)s"
    params = {}
    params['id'] = session.get("user_id")

    db = rundbquery(query, params)
    for row in db:
        if row[0] == 0 or row[0] == "" or row[0] is None:
            return 0
        else:
            return 1


def rundbquery(query, params):
    """Run a given SQL query"""
    conn = pymysql.connect(host, user=user, port=port, passwd=password, db=dbname, autocommit=False)

    try:
        cursor = conn.cursor()
        # Add Query parameters and run it
        if (params == ""):
            cursor.execute(query)
        else:
            cursor.execute(query, params)
    except:
        conn.rollback()
        raise
    else:
        conn.commit()
        conn.close()

    return cursor
