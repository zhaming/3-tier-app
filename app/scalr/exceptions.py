#coding:utf-8
from __future__ import unicode_literals


class NoConnectionEstablished(Exception):
    """
    Raised when no connection could be established
    """
    def __init__(self, connection_info, error):
        super(NoConnectionEstablished, self).__init__()
        self.connection_info = connection_info
        self.error = error
