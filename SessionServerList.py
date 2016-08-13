from SessionServerInfo import SessionServerInfo

class SessionServerList(list):
    """
    A class that maintains a sorted list of SessionServerInfo objects.

    With the exception of the fact that the methods in this class only
    work with SessionServerInfo objects and that the insert(), reverse()
    and sort() methods are unavailable (they don't make sense in a
    #sorted list), this class maintains the API exposed by the list() class.
    """

    def __init__(self, iterable=[]):
        # Confirm all items in iterable are of type SessionServerInfo
        for item in iterable:
            assert isinstance(item, SessionServerInfo)
        super().__init__(iterable)

        if iterable is not None:
            self._sort_by_hostname()

    def append(self, item):
        assert isinstance(item, SessionServerInfo)
        super().append(item)
        self._sort_by_hostname()

    def extend(self, iterable):
        for item in iterable:
            assert isinstance(item, SessionServerInfo)
        super().extend(iterable)
        self._sort_by_hostname()


    def _sort_by_hostname(self):
        """
        A private method that sorts the underlying list in-place
        by the hostname of the SessionServerInfo object.

        :return:
        """
        super().sort(key=lambda x: x.hostname)


    # Mark these mothods not-implemented as they don't make sense
    # for a list that must always be sorted by the hostname.
    def insert(self, index, item):
        raise NotImplementedError

    def reverse(self):
        raise NotImplementedError

    def sort(key=None, reverse=False):
        raise NotImplementedError

