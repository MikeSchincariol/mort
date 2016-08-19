#!/usr/bin/env python3

import sys
import string
import socket
import errno
import select
import threading
import logging
import logging.handlers
import json
import subprocess
import re

import ServerAnnounceTask


def main():
    """

    :return:
    """

    # Configure a log file, to write log messages into, that auto-rotates when
    # it reaches a certain size.
    rotating_log_handler = logging.handlers.RotatingFileHandler(filename='mort_session_server.log',
                                                                mode='a',
                                                                maxBytes=1E6,
                                                                backupCount=3)
    logging.basicConfig(format="{asctime:11} :{levelname:10}: {name:22}({lineno:4}) - {message}",
                        style="{",
                        level=logging.DEBUG,
                        handlers=[rotating_log_handler])

    # Get a new logger to use
    log = logging.getLogger("mort_session_server")

    # Print a startup banner to mark the beginning of logging
    log.info("")
    log.info("--------------------------------------------------------------------------------")
    log.info("Mort session-server starting up...")


    my_hostname = socket.gethostname()
    my_ip_address = socket.gethostbyname(my_hostname)
    my_port = 42124

    # Open a TCP socket to listen for service requests.
    # NOTE: The port is not important because the actual port used
    #       will be communicated to the launcher via a the
    #       session server announce message.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Attempt to bind to a socket at TCP:42124. However, if that
    # port is already taken, that is not a problem, try the next
    # port in sequence until we find one, or, we run out of ports
    # to try (in this case, we stop if a port hasn't been found
    # by port 59999)
    while True:
        if my_port <= 59999:
            try:
                sock.bind((my_ip_address, my_port))
                log.info("Bound to TCP socket @ {0}:{1}".format(my_ip_address, my_port))
                break
            except OSError as ex:
                if ex.errno == errno.EADDRINUSE:
                    my_port += 1
                else:
                    raise
        else:
            log.critical("Could not find an open port in the range 42124 to 59999.")
            log.critical(" Session server exiting.")
            sys.exit(1)

    # Start the session-server announce thread
    log.info("Starting session-server announce task")
    announce_task = ServerAnnounceTask.ServerAnnounceTask(my_hostname, my_ip_address, my_port)
    announce_task.start()

    # Start listening for service requests
    sock.setblocking(False)
    sock.listen(5)

    # Enter the service loop
    log.info("Starting service loop")
    while True:
        # Wait for connection requests
        # :NOTE: Since only the socket is in the following call to select(), when
        #        select returns, we know that it must be for a connection request.
        robj, wobj, xobj = select.select([sock], [], [])

        # Accept it and spawn a thread to handle the connection request.
        conn, remote_addr = sock.accept()
        log.info("Accepted connection from: {}".format(remote_addr))
        handler_thread_name = "handle_socket_{}_{}".format(remote_addr[0].replace(".", "_"),
                                                           remote_addr[1])
        log.info("Spawning socket handler thread: {}".format(handler_thread_name))

        new_thread = threading.Thread(target=handle_socket_task,
                                      name=handler_thread_name,
                                      args=(conn, remote_addr),
                                      daemon=True)
        new_thread.start()

        # At this point, the server is free to wait for another connection
        # without blocking on any requests.


    # :TODO: How do shut down?
    # :TODO: Need to implement signal handling logic....



def handle_socket_task(sock, remote_addr):
    """

    :param sock:
    :param remote_addr:
    :return:
    """

    # :TODO: Should this be a separate file like the other tasks?

    # Configure logging
    log = logging.getLogger("{}".format(threading.current_thread().name))
    log.debug("Starting up...")

    # Read out the message data
    log.debug("Reading out request message...")
    msg = sock.recv(16384)
    log.debug("Received {0} bytes".format(len(msg)))
    msg = msg.decode('utf8')

    # Break the response down into its key/value pairs
    log.debug("Parsing message...")
    msg_lines = msg.splitlines()
    msg_fields = {}
    for msg_line in msg_lines:
        msg_field = msg_line.split(':', 1)
        msg_fields[msg_field[0]] = msg_field[1]

    # Check for the correct message type. If this isn't a list_active_sessions
    # message then discard it and move on.
    if "msg_type" in msg_fields.keys():
        if msg_fields["msg_type"] == "get_active_sessions":
            log.debug("Message is good")
            # Get a list of all the Xvnc processes running
            log.debug("Querying list of Xvnc processes from OS...")
            process_list = subprocess.check_output(["ps", "--no-header", "-ww", "-C", "Xvnc", "-o", "user,pid,args"])
            process_list = process_list.decode('utf8')
            process_list = process_list.splitlines()

            # Parse out the server information from the listing returned
            active_sessions = []
            log.debug("Parsing Xvnc process list...")
            for process in process_list:
                matches = re.search(r"^(?P<username>\w+)\s+(?P<pid>\d+)\s+(?P<exe>[\w/]+)\s+(?P<args>.+$)",
                                    process)
                username, pid, exe, args = matches.group("username", "pid", "exe", "args")

                # Get the display number from the args
                match = re.search(r"^:(?P<display_number>\d+)", args)
                if match is None:
                    display_number = 0
                else:
                    display_number = match.group("display_number")

                # Get the display name from the args
                match = re.search(r"-desktop\s+(?P<display_name>[ a-zA-Z0-9/\-|.:()]+?)\s+(-|$)", args)
                if match is None:
                    display_name = "{0}:{1}".format(username, display_number)
                else:
                    display_name = match.group("display_name")

                # Get the geometry from the args
                match = re.search(r"-geometry\s+(?P<geometry>[ 0-9x]+?)\s+(-|$)", args)
                if match is None:
                    geometry = "Unknown"
                else:
                    geometry = match.group("geometry")

                # Get the pixelformat from the args, which if not present, can be inferred
                # from the depth parameter if it is present in the args
                # :NOTE: Consult the Xvnc man page for details on the defaults for
                #        pixelformat and depth.
                match = re.search(r"-pixelformat\s+(?P<pixelformat>[a-zA-Z0-9]+?)\s+(-|$)", args)
                if match is None:
                    match = re.search(r"-depth\s+(?P<depth>[0-9]+?)\s+(-|$)", args)
                    if match is None:
                        # Assume default depth of 24 and default pixelformat of RGB888
                        pixelformat = "RGB888"
                    else:
                        depth = match.group("depth")
                        if depth == "8":
                            pixelformat = "BGR233"
                        elif depth == "15":
                            # :NOTE: The Xvnc man page doesn't give a default for 15bpp
                            pixelformat = "Unknown"
                        elif depth == "16":
                            pixelformat = "RGB565"
                        elif depth == "24":
                            pixelformat = "RGB888"
                        else:
                            pixelformat = "Unknown"
                else:
                    pixelformat = match.group("pixelformat").upper()

                # Add the session to the list of sessions to return to the client.
                new_session_info = {}
                new_session_info["username"] = username
                new_session_info["pid"] = pid
                new_session_info["display_number"] = display_number
                new_session_info["display_name"] = display_name
                new_session_info["geometry"] = geometry
                new_session_info["pixelformat"] = pixelformat

                active_sessions.append(new_session_info)

            log.debug("Found {0} Xvnc servers running.".format(len(active_sessions)))

            # Encode the list of active sessions as JSON and send it
            # to the client.
            log.debug("Preparing response message...")
            active_sessions_json = json.dumps(active_sessions)
            resp = ("msg_type:active_sessions_list\n"
                    "active_sessions:{0}".format(active_sessions_json))
            log.debug("Sending response message...")
            sock.sendall(resp.encode('utf8'))

        else:
            # Discard message; not a "active_sessions_list" message
            msg = ("Invalid get_active_sessions message from {0}:{1}."
                   " Invalid msg_type value."
                   " Discarding".format(remote_addr[0],
                                        remote_addr[1]))
            log.warning(msg)
    else:
        # Discard message; no msg_type field found.
        msg = ("Invalid get_active_sessions message from {0}:{1}."
               " Invalid msg_type value."
               " Discarding".format(remote_addr[0],
                                    remote_addr[1]))
        log.warning(msg)

    # Close the socket as we are done with it.
    log.debug("Closing socket...")
    sock.close()
    log.debug("Done.")


if __name__ == "__main__":
    main()