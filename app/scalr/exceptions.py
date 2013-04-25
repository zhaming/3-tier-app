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
        super(NoConnectionEstablished, self).__init__()
        self.connection_info = connection_info
        self.error = error


class NoHost(NoConnectionEstablished):
    """
    Raised when we try to connect to an non-existing Host.
    """
    pass


class InvalidCredentials(NoConnectionEstablished):
    """
    Raised when our credentials are refused by the MySQL host.
    """
    pass
