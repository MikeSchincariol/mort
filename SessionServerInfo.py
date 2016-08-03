import datetime

class SessionServerInfo(object):
    """
    A class to hold information that describes a session-server.
    """

    def __init__(self, hostname=None, ip_address=None, port=None, last_seen=None):
        """
        Class constructor.

        :param hostname: String hostname of the session server. Optional.
        :param ip_address:  String ip address of the session server. Optional.
        :param port: Integer port of the session server. Optional.
        :param last_seen: DateTime last_seen time of the last announcement from the session server. Optional.
        :return:
        """

        # Check appropriate types are passed in
        assert hostname is None or isinstance(hostname, str)
        assert ip_address is None or isinstance(ip_address, str)
        assert port is None or isinstance(port, int)
        assert last_seen is None or isinstance(last_seen, datetime.datetime)

        self._hostname = hostname
        self._ip_address = ip_address
        self._port = port
        self._last_seen = last_seen


    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, val):
        assert isinstance(val, str)
        self._hostname = val

    @property
    def ip_address(self):
        return self._ip_address

    @ip_address.setter
    def ip_address(self, val):
        assert isinstance(val, str)
        self._ip_address = val

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, val):
        assert isinstance(val, int)
        self._port = val

    @property
    def last_seen(self):
        return self._last_seen

    @last_seen.setter
    def last_seen(self, val):
        assert isinstance(val, datetime.datetime)
        self._last_seen = val
