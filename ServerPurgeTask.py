import threading
import time
import datetime
import logging


class ServerPurgeTask(threading.Thread):
    """
    A class that runs as a thread to clean out session-servers from the
    list of known session-servers if an announce message hasn't been
    received within a specific time interval from a session-server.
    """

    def __init__(self, known_servers, known_servers_cv):
        """
        Class constructor

        :param known_servers: A Python list of SessionSeverInfo objects.
        :param known_servers_cv: A threading.Condition object used to arbitrate access to the known_servers
                                 list and to notify other threads that the known_servers list was updated.
        """
        # Give a name to this thread and make it a daemon so it
        # doesn't prevent the caller from exiting.
        super().__init__(name="purge_thread", daemon=True)

        # Configure logging
        self.log = logging.getLogger("ServerPurgeTask")
        self.log.info("Mort ServerPurgeTask starting up...")

        # Store the references to the known_servers list and it's associated
        # lock for use later.
        self.known_servers = known_servers
        self.known_servers_cv = known_servers_cv


    def run(self):
        """
        Handles iterating over the known_servers list and purging session-servers
        that haven't been seen within a specific time interval.
        :return:
        """
        while True:
            # Grab the lock before doing anything with the list since the list
            # is shared between threads.
            with self.known_servers_cv:
                known_servers_list_updated = False
                for server in self.known_servers[:]:
                    # If we haven't seen an announce message from the server in
                    # the last 30 seconds, remove it from the list.
                    delta = datetime.datetime.now() - server.last_seen
                    if delta.seconds > 30:
                        self.known_servers.remove(server)
                        self.log.info("Removed host: {0} ({1}:{2}) last seen: {3}".format(server.hostname,
                                                                                          server.ip_address,
                                                                                          server.port,
                                                                                          server.last_seen))
                        known_servers_list_updated = True

                # If changes were made to the known_servers list, notify watchers.
                if known_servers_list_updated:
                    self.known_servers_cv.notify_all()

            # Chill for a bit before checking again...
            time.sleep(10)
