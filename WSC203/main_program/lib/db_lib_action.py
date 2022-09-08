#!/usr/bin/env python3
# coding: UTF-8

import sqlite3
from contextlib import closing
import pathlib
import logging
import os

db_name = 'database_action.db'
db_file_path = str(pathlib.Path(__file__).parent) + '/' + db_name  # DB路徑
# print(db_file_path)
logger = logging.getLogger("app." + __name__)
# tmp_db_uri = 'file:database?mode=memory&cache=shared'
tmp_db_uri = '/dev/shm/' + db_name
action_column_tmp = "uid,conn_status"


def drop_action_table_tmp():
    cmd = "DROP TABLE IF EXISTS action_tmp;"
    with closing(sqlite3.connect(tmp_db_uri)) as con:
        with con:
            with closing(con.cursor()) as cursor:
                try:
                    cursor.execute(cmd)
                except:
                    os.remove(tmp_db_uri)


def create_action_table_tmp():
    cmd = "DROP TABLE IF EXISTS action_tmp;"
    with closing(sqlite3.connect(tmp_db_uri)) as con:
        with con:
            with closing(con.cursor()) as cursor:
                cursor.execute(cmd)

    cmd = "CREATE TABLE IF NOT EXISTS action_tmp (" \
          "uid INTEGER UNIQUE PRIMARY KEY," \
          "conn_status INTEGER)"
    with closing(sqlite3.connect(tmp_db_uri)) as con:
        with con:
            with closing(con.cursor()) as cursor:
                cursor.execute(cmd)
                add_action_tmp()


def add_action_tmp():
    dict_data = {'uid': 1, 'conn_status': 0}
    cmd = "INSERT INTO action_tmp ({}) VALUES ({},{})" \
        .format(action_column_tmp, dict_data['uid'], dict_data['conn_status'])
    # print(cmd)
    with closing(sqlite3.connect(tmp_db_uri)) as con:
        with con:
            with closing(con.cursor()) as cursor:
                try:
                    cursor.execute(cmd)
                    return True
                except sqlite3.Error as e:
                    print('add_action_tmp:{}'.format(e))
                    return False


def get_action_tmp():
    cmd = "SELECT conn_status " \
          "FROM action_tmp WHERE uid = 1"
    # print(cmd)
    with closing(sqlite3.connect(tmp_db_uri)) as con:
        with con:
            with closing(con.cursor()) as cursor:
                cursor.execute(cmd)
                data = cursor.fetchone()

    if data:
        return {'conn_status': data[0]}
    else:
        return


def update_action_tmp(update_dict):
    cmd = "UPDATE action_tmp SET "
    cmd_list = []
    for key, value in update_dict.items():
        if isinstance(value, str):
            cmd_list.append("{}='{}'".format(key, value))
        else:
            cmd_list.append("{}={}".format(key, value))

    cmd += ','.join(cmd_list)
    cmd += " WHERE uid={}".format(1)
    # print(cmd)
    with closing(sqlite3.connect(tmp_db_uri)) as con:
        with con:
            with closing(con.cursor()) as cursor:
                try:
                    cursor.execute(cmd)
                    return True
                except sqlite3.Error as e:
                    print('update_action_tmp:{}'.format(e))
                    return False


if __name__ == "__main__":
    # drop_action_table_tmp()
    # create_action_table_tmp()
    print(get_action_tmp())
    update_action_tmp({'conn_status': 1})
