import threading
import socket
import datetime
import logging
import select

import SessionServerInfo

class LauncherAnnounceTask(threading.Thread):
    """
    A class that runs as a thread and handles receiving the server-announce
    messages that arrive
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
        super().__init__(name="announce_thread", daemon=True)

        # Configure logging
        self.log = logging.getLogger("LauncherAnnounceTask")
        self.log.info("Mort LauncherAnnounceTask starting up...")

        # Store up the instance data passed in for use later
        self.known_servers = known_servers
        self.known_servers_cv = known_servers_cv

        # A socket to watch for session-server announce messages
        self.announce_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.announce_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.announce_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Setup the announce socket to watch for server announce messages.
        try:
            #self.announce_sock.bind(('<broadcast>', 42124))
            self.announce_sock.bind(('0.0.0.0', 42124))
        except OSError as ex:
            msg = ("Unable to create broadcast socket."
                   " Error No: {0}"
                   " Error Msg: {1}".format(ex.errno, ex.strerror))
            self.log.critical(msg)
            raise


    def run(self):
        """
        Handles reception of session-server announce messages, updating
        the list of known session-servers and the Treeview component
        that displays the known session-servers on the GUI.
        """
        while True:
            # Wait for data to arrive on the announce_sock objectx
            robj, wobj, xobj = select.select([self.announce_sock], [], [])

            # Read the packet from the socket.
            # :NOTE: Since the announce_sock is the ONLY item in the call to select above,
            #        if we get to this point, we know it's because the announce_sock
            #        had data to read.
            msg, remote_addr = self.announce_sock.recvfrom(4096)
            msg = msg.decode('utf8')

            # Break the message down into its key/value pairs
            msg_lines = msg.splitlines()
            msg_fields = {}
            for msg_line in msg_lines:
                msg_field = msg_line.split(':')
                msg_fields[msg_field[0]] = msg_field[1]

            # Check for the correct message type. If this isn't a server-announce
            # message then discard it and move on.
            # :WARN: Must obtain the lock on the known_server variable before
            #        interacting with it.
            if "msg_type" in msg_fields.keys():
                if msg_fields["msg_type"] == "session_server_announce":
                    with self.known_servers_cv:
                        known_servers_list_updated = False
                        for known_server in self.known_servers:
                            if known_server.ip_address == msg_fields["ip_address"]:
                                # We've seen this server before. Update its information in
                                # case it has changed
                                if known_server.hostname != msg_fields["hostname"]:
                                    known_server.hostname = msg_fields["hostname"]
                                    known_servers_list_updated = True

                                if known_server.port != int(msg_fields["port"]):
                                    known_server.port = int(msg_fields["port"])
                                    known_servers_list_updated = True

                                known_server.last_seen = datetime.datetime.now()
                                break
                        else:
                            # Server is new so add it to the known_servers list.
                            new_server = SessionServerInfo.SessionServerInfo(msg_fields["hostname"],
                                                                             msg_fields["ip_address"],
                                                                             int(msg_fields["port"]),
                                                                             datetime.datetime.now())
                            self.known_servers.append(new_server)
                            self.log.info("Added host: {0} ({1}:{2})".format(new_server.hostname,
                                                                             new_server.ip_address,
                                                                             new_server.port))
                            known_servers_list_updated = True

                        # If changes were made to the known_servers list, notify watchers.
                        if known_servers_list_updated:
                            self.known_servers_cv.notify_all()

                else:
                    # Discard message; not a "session_server_announce" message
                    msg = ("Invalid session server announce message from {0}:{1}."
                           " Invalid msg_type value."
                           " Discarding".format(remote_addr[0],
                                                remote_addr[1]))
                    self.log.warning(msg)
            else:
                # Discard message; no msg_type field found.
                msg = ("Invalid session server announce message from {0}:{1}."
                       " Missing msg_type field."
                       " Discarding".format(remote_addr[0],
                                            remote_addr[1]))
                self.log.warning(msg)


