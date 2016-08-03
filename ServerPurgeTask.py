import threading
import socket
import time
import datetime


class ServerPurgeTask(threading.Thread):
    """
    A class that runs as a thread to clean out session-servers from the
    list of known session-servers if an announce message hasn't been
    received within a specific time interval.
    """

    def __init__(self, known_servers, known_servers_lock):
        """
        Class constructor
        :param known_servers: A list of session-servers to iterate over.
        :param known_servers_lock: A threading.Lock object related to the known-servers list.
        """
        # Give a name to this thread and make it a daemon so it
        # doesn't prevent the caller from exiting.
        super().__init__(name="purge_thread", daemon=True)

        # Store the references to the known_servers list and it's associated
        # lock for use later.
        self.known_servers = known_servers
        self.known_servers_lock = known_servers_lock



    def run(self):
        """
        Handles iterating over the known_servers list and purging session-servers
        that haven't been seen within a specific time interval.
        :return:
        """
        while True:
            with self.known_servers_lock:
                for server in self.known_servers[:]:
                    # If we haven't seen an announce message from the server in
                    # the last 30 seconds, remove it from the list.
                    delta = datetime.datetime.now() - server.last_seen
                    if delta.seconds > 30:
                        self.known_servers.remove(server)

            # Chill for a bit before checking again...
            time.sleep(10)
