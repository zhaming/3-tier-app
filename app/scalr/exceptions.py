#coding:utf-8

class NoConnectionInfo(Exception):
    """
    Raised when connection info hasn't been made available
    """


class NoConnectionEstablished(Exception):
    """
    Raised when no connection could be established
    """
    def __init__(self, connection_info, error):
        self.connection_info = connection_info
        self.error = error


class NoHost(NoConnectionEstablished):
    pass


class InvalidCredentials(NoConnectionEstablished):
    pass
