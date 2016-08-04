import sys
import socket
import errno
import select
import time
import datetime
import threading
import signal
import logging
import logging.handlers

import SessionServerInfo
import ServerPurgeTask


def main():
    """

    :return:
    """

    # Configure a log file, to write log messages into, that auto-rotates when
    # it reaches a certain size.
    rotating_log_handler = logging.handlers.RotatingFileHandler(filename='mort_session_launcher.log',
                                                                mode='a',
                                                                maxBytes=1E6,
                                                                backupCount=3)
    # Configure a stdout log handler to print all messages
    stdout_log_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_log_handler.setLevel(logging.DEBUG)

    # Configure a stderr log handler to print only ERROR messages and abve
    stderr_log_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_log_handler.setLevel(logging.ERROR)

    logging.basicConfig(format="{asctime:11} :{levelname:10}: {name:22}({lineno:4}) - {message}",
                        style="{",
                        level=logging.DEBUG,
                        handlers=[stdout_log_handler, stderr_log_handler, rotating_log_handler])

    # Get a new logger to use
    log = logging.getLogger("mort_session_launcher")

    # Print a startup banner to mark the beginning of logging
    log.info("")
    log.info("--------------------------------------------------------------------------------")
    log.info("Mort session-launcher starting up...")

    # A list of session-servers already seen and a lock to use
    # to arbitrate access from different threads
    known_servers = []
    known_servers_lock = threading.Lock()

    # A socket to watch for session-server announce messages
    announce_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    announce_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    announce_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

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
    # list_task = threading.Thread(None,
    #                              target=print_session_server_list,
    #                              args=(known_servers, known_servers_lock))
    # list_task.start()

    # Setup keyboard input....


    # Enter the main event loop to wait for keyboard or socket events.
    while True:
        robj, wobj, xobj = select.select([announce_sock], [], [])
        for obj in robj:
            if obj == announce_sock:
                handle_server_announce_msg(announce_sock, known_servers, known_servers_lock)
            else:
                pass


def handle_server_announce_msg(announce_sock, known_servers, known_servers_lock):
    """

    :param announce_sock:
    :param known_servers:
    :param known_servers_lock:
    :return:
    """
    # Get the logger to use
    log = logging.getLogger("mort_session_launcher")

    # Read the packet from the socket.
    msg, remote_addr = announce_sock.recvfrom(4096)
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
                    log.info("Added host: {0} ({1}:{2})".format(new_server.hostname,
                                                                new_server.ip_address,
                                                                new_server.port))
        else:
            # Discard message; not a "session_server_announce" message
            msg = ("Invalid session server announce message from {0}:{1}."
                   " Invalid msg_type value."
                   " Discarding".format(remote_addr[0],
                                        remote_addr[1]))
            log.warning(msg)
    else:
        # Discard message; no msg_type field found.
        msg = ("Invalid session server announce message from {0}:{1}."
               " Missing msg_type field."
               " Discarding".format(remote_addr[0],
                                    remote_addr[1]))
        log.warning(msg)


def print_session_server_list(known_servers, known_servers_lock):
    """

    :param known_servers:
    :param known_servers_lock:
    :return:
    """
    # Get the logger to use
    log = logging.getLogger("mort_session_launcher")

    # Loop over the known session-servers and print out their details.
    while True:
        with known_servers_lock:
            log.info("Session Server Listing @ {}\n".format(datetime.datetime.now()))
            for server in known_servers:
                log.info("\tServer: {0} ({1}:{2})\n".format(server.hostname,
                                                         server.ip_address,
                                                         server.port))

        time.sleep(1)



if __name__ == "__main__":
    main()