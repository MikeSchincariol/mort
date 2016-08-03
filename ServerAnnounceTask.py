import threading
import socket
import time


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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


    def run(self):
        """
        Handles constructing an announce message and sending it.
        Then pauses a set amount of time before sending another message.
        :return:
        """
        while True:
            self.sock.sendto(self.msg.encode('utf8'), ("<broadcast>", 42124))
            time.sleep(10)


if __name__ == "__main__":
    task = ServerAnnounceTask('test-session_server', '192.168.43.12', '23234')
    task.start()
    task.join()
