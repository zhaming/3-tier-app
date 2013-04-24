#coding:utf-8
import os

from scalr import exceptions
from scalr import db

CONFIG_STRUCTURE = (
    ('mysql-username', 'username'), ('mysql-password', 'password'),
    ('mysql-master', '_master'), ('mysql-slave', '_slave'),
 )

def parse_config(path):
    kwargs = {}

    for fname, attr in CONFIG_STRUCTURE:
        try:
            with open(os.path.join(path, fname)) as f:
                kwargs[attr] = f.read().strip()
        except IOError:
            raise exceptions.NoConnectionInfo()

    return db.ConnectionInfo(**kwargs)
