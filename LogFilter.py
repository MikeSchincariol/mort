import logging

class Filter(object):
    """
    A class used by the logging module for filtering log messages by name prefix.
    This is opposite to how the filter in the logging module works.
    """

    def __init__(self, name=''):
        """
        Returns an instance of the Filter class.

        :param name: If name is specified, it names a logger, together with its children,
                     that will have its log events filtered out. If name is the empty string,
                     it will discard every event. The later behavior is not useful but
                     mimics carries through the pattern of doing the exact opposite of what
                     the filter class in the logging module does.
        """
        assert isinstance(name, str)
        self.filter_name_parts = name.split(".")


    def filter(self, record):
        """
        Examines the hierarchical name of the logger in the log record. If the
        hierarchical filter name matches the start of the hierarchical logger name,
        the log message is discarded.

        :param record: A logging.LogRecord
        :return: 0 to discard log record. 1 to keep the log record.
        """

        assert isinstance(record, logging.LogRecord)

        # Handle the special case of the filter name being the empty string.
        if self.filter_name_parts[0] == '':
            return 0

        # Split the hierarchical name of the logger into its parts and then compare
        # it against the hierarchical name of the filter. If there is a match for all
        # the items in the filter name, then, discard the log event.
        record_name_parts = record.name.split(".")

        # If the record name has fewer path components then the filter path,
        # then there can never be a match, so, let it through.
        if len(record_name_parts) < len(self.filter_name_parts):
            return 1

        for idx, part in enumerate(self.filter_name_parts):
            if part != record_name_parts[idx]:
                return 1
        else:
            return 0
