#coding:utf-8
from __future__ import unicode_literals
import os

from scalr import db


ENV_CONFIG_STRUCTURE = (
    ('APP_MYSQL_USERNAME', 'username'), ('APP_MYSQL_PASSWORD', 'password'),
    ('APP_MYSQL_MASTER', '_master'), ('APP_MYSQL_SLAVE', '_slave')
)


FILE_CONFIG_STRUCTURE = (
    ('mysql-username', 'username'), ('mysql-password', 'password'),
    ('mysql-master', '_master'), ('mysql-slave', '_slave'),
)


def parse_config(path):
    """
    Parse config files at `path` with a structure as defined in
    CONFIG_STRUCTURE
    """
    kwargs = {}

    try:
        for fname, attr in FILE_CONFIG_STRUCTURE:
            with open(os.path.join(path, fname)) as cnf_file:
                kwargs[attr] = cnf_file.read().strip()
    except IOError:
        return None

    return db.ConnectionInfo(**kwargs)


def load_config_from_env():
    kwargs = {}

    try:
        for var, attr in ENV_CONFIG_STRUCTURE:
            kwargs[attr] = os.environ[var]
    except KeyError:
        return None

    return db.ConnectionInfo(**kwargs)
