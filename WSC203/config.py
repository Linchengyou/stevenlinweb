# -*- coding: utf-8 -*-
import os
import pathlib
import json

product_info_path = '/etc/product-info'
product_info = json.loads(pathlib.Path(product_info_path).read_text())
APP_NAME = product_info['model']['name'].upper()
VERSION = product_info['model']['version'].upper()

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess1'
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'mydb.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True


# available languages
LANGUAGES = {
    'en': 'English',
    'zh': '中文'
}

app_config_path = '{}/main_program/config/config.json'.format(basedir)
app_lib_path = '{}/main_program/lib/'.format(basedir)
web_QC_path = '{}/QC/'.format(basedir)
web_app_lib_path = '{}/app/lib/'.format(basedir)
service_name = 'app'
BOOTSTRAP_SERVE_LOCAL = True
