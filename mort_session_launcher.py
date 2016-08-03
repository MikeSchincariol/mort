import sys
import socket
import errno
import select
import time
import datetime
import threading
import signal

import SessionServerInfo
import ServerPurgeTask

# Some global variables...

# A list of session-servers already seen and a lock to use
# to arbitrate access from different threads
known_servers = []
known_servers_lock = threading.Lock()

# A socket to watch for session-server announce messages
announce_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
announce_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
announce_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


def startup():
    # Setup the announce socket to watch for server announce messages.
    try:
        announce_sock.bind(('<broadcast>', 42124))
    except OSError as ex:
        if ex.errno == errno.EADDRINUSE:
            print("Could not open a socket on <broadcast>:42124 as it is already in use.\n")
            print("Session launcher exiting.\n")
            sys.exit(1)
        else:
            raise

    # Start a thread to periodically clean the list of session-servers to
    # remove those that haven't been heard from in a while.
    purge_task = ServerPurgeTask.ServerPurgeTask(known_servers, known_servers_lock)
    purge_task.start()

    # Temporary thread to show server list repeatedly each second
    list_task = threading.Thread(None, target=print_session_server_list)
    list_task.start()

    # Setup keyboard input....


    # Enter the main event loop to wait for keyboard or socket events.
    while True:
        robj, wobj, xobj = select.select([announce_sock], [], [])
        for obj in robj:
            if obj == announce_sock:
                handle_server_announce_msg()
            else:
                pass


def handle_server_announce_msg():
    """

    :return:
    """
    # Read the packet from the socket.
    msg = announce_sock.recv(4096)
    msg = msg.decode('utf8')

    # Break the message down into its key/value pairs
    msg_lines = msg.splitlines()
    msg_fields = {}
    for msg_line in msg_lines:
        msg_field = msg_line.split(':')
        msg_fields[msg_field[0]] = msg_field[1]

    # Check for the correct message type. If this isn't a server-announce
    # message then discard it and move on.
    if "msg_type" in msg_fields.keys():
        if msg_fields["msg_type"] == "session_server_announce":
            with known_servers_lock:
                for known_server in known_servers:
                    if known_server.ip_address == msg_fields["ip_address"]:
                        # We've seen this server before. Update its information in
                        # case it has changed
                        known_server.hostname = msg_fields["hostname"]
                        known_server.port = int(msg_fields["port"])
                        known_server.last_seen = datetime.datetime.now()
                        break
                else:
                    # Server is new so add it to the known_servers list.
                    new_server = SessionServerInfo.SessionServerInfo(msg_fields["hostname"],
                                                                     msg_fields["ip_address"],
                                                                     int(msg_fields["port"]),
                                                                     datetime.datetime.now())
                    known_servers.append(new_server)

        else:
            # :TODO: Improve information by including sending server/port that issued
            #        the invalid message
            print("Invalid session server announce message. Discarding. \n")
    else:
        # :TODO: Improve information by including sending server/port that issued
        #        the invalid message
        print("Invalid session server announce message. Discarding. \n")




def print_session_server_list():
    while True:
        with known_servers_lock:
            print ("Session Server Listing @ {}\n".format(datetime.datetime.now()))
            for server in known_servers:
                print("\tHostname: {0}  IP: {1}  Port: {2}\n".format(server.hostname,
                                                                     server.ip_address,
                                                                     server.port))

        time.sleep(1)



if __name__ == "__main__":
    startup()