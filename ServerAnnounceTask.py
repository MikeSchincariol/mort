import threading
import socket
import time
import random
import string
import logging


class ServerAnnounceTask(threading.Thread):
    """
    A class that runs as a thread and handles sending server-announce
    messages at repetitive intervals.
    """

    def __init__(self, announce_hostname, announce_ip_address, announce_port):
        """
        Class constructor

        :param announce_hostname: The string hostname of the session server to announce.
        :param announce_ip_address: The string IP address of the session server to announce.
        :param announce_port: The integer port the session-server is listening on.
        """
        # Give a name to this thread and make it a daemon so it
        # doesn't prevent the caller from exiting.
        super().__init__(name="announce_thread", daemon=True)

        # Configure logging
        self.log = logging.getLogger("ServerAnnounceTask")
        self.log.info("Mort ServerAnnounceTask starting up...")

        # Store up the data for the announce message
        self.ip_address = announce_ip_address
        self.hostname = announce_hostname
        self.port = announce_port
        self.msg = ("msg_type:session_server_announce\n"
                    "hostname:{0}\n"
                    "ip_address:{1}\n"
                    "port:{2}\n".format(self.hostname,
                                        self.ip_address,
                                        self.port))

        # Get a persistent UDP socket for sending the messages
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except OSError as ex:
            msg = ("Unable to create broadcast socket."
                   " Error No: {0}"
                   " Error Msg: {1}".format(ex.errno, ex.strerror))
            self.log.critical(msg)


    def run(self):
        """
        Handles constructing an announce message and sending it.
        Then pauses a set amount of time before sending another message.
        """
        while True:
            try:
                self.sock.sendto(self.msg.encode('utf8'), ("<broadcast>", 42124))
            except OSError as ex:
                msg = ("Unable to send session-server announce message."
                       " Error No: {0}"
                       " Error Msg: {1}".format(ex.errno, ex.strerror))
                self.log.critical(msg)
            finally:
                time.sleep(10)


if __name__ == "__main__":
    # For testing purposes, each time this thread is started as the
    # main program, kick off a server with a random information
    # This will allow multiple announce tasks to be started, each
    # with their own name, that can be used to simultanously announce
    # to a launcher.
    random_hostname = "test_session_server-"
    for c in range(0, 8):
        random_hostname += random.choice((string.ascii_letters + string.digits))

    random_ip_address = "192.168.{0}.{1}".format(random.randint(1, 254),
                                                 random.randint(1, 254))

    random_port = random.randint(42124, 59999)

    task = ServerAnnounceTask(random_hostname, random_ip_address, random_port)
    task.start()
    task.join()
