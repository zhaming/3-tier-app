#coding:utf-8
from __future__ import unicode_literals
import os


try:
    TEST_DB_CONFIG = {
        'username': os.environ['TEST_MYSQL_USERNAME'],
        'password': os.environ['TEST_MYSQL_PASSWORD'],
        '_master': os.environ["TEST_MYSQL_MASTER"],
        '_slave': os.environ['TEST_MYSQL_SLAVE'],
    }
except KeyError:
    TEST_DB_CONFIG = {
        '_master': 'localhost',
        '_slave': 'localhost',
        'username': 'root',
        'password': 'APP_TEST_PASSWORD',
    }


TEST_DB_CONFIG.update({
    'database': 'APP_TEST_DATABASE'
})
