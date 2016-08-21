#!/usr/bin/env python3

import sys
import os
import signal
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
import configparser

import ServerAnnounceTask
import CreateNewVNCServer


def main():
    """

    :return:
    """
    # Determine where the source code is to be found
    # :NOTE: Refer to documentation of sys.path for why this works.
    SRC_DIR = os.path.abspath(sys.path[0])

    # Open the config file for reading
    cfg = configparser.ConfigParser()
    cfg.read(SRC_DIR+"/server.ini")

    # A dictionary to map the log level string from the config file, to
    # the log level constant used by the Python logging module.
    loglevel_string_to_constant = {"DEBUG":    logging.DEBUG,
                                   "INFO":     logging.INFO,
                                   "WARNING":  logging.WARNING,
                                   "ERROR":    logging.ERROR,
                                   "CRITICAL": logging.CRITICAL}

    # Configure a log file, to write log messages into, that auto-rotates when
    # it reaches a certain size.
    rotating_log_handler = logging.handlers.RotatingFileHandler(filename='mort_session_server.log',
                                                                mode='a',
                                                                maxBytes=1E6,
                                                                backupCount=3)
    logging.basicConfig(format="{asctime:11} :{levelname:10}: {name:22}({lineno:4}) - {message}",
                        style="{",
                        level=loglevel_string_to_constant[cfg.get("LOGGING", "file_level", fallback="DEBUG")],
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



def get_xvnc_process_info():
    """
    Queries the OS for a list of Xvnc processes that are running
    and returns details of each process, such as its PID and the
    command line args each process was called with.
    :return:
    """

    # Configure logging
    log = logging.getLogger("get_xvnc_process_info")

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
    return active_sessions


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
        log.debug("Message type: {}".format(msg_fields["msg_type"]))

        if msg_fields["msg_type"] == "get_active_sessions":
            # Get a list of all the Xvnc processes running
            active_sessions = get_xvnc_process_info()
            # Encode the list of active sessions as JSON and send it to the client.
            log.debug("Preparing response message...")
            active_sessions_json = json.dumps(active_sessions)
            resp = ("msg_type:active_sessions_list\n"
                    "active_sessions:{0}\n".format(active_sessions_json))
            log.debug("Sending response message...")
            sock.sendall(resp.encode('utf8'))

        elif msg_fields["msg_type"] == "start_active_session":
            # Pull out the params to call vncserver with

            # Confirm there are no vncservers running with the requested display
            active_sessions = get_xvnc_process_info()
            for session in active_sessions:
                if session["display_number"] == msg_fields["display_number"]:
                    log.debug("Found session already running on display {}".format(msg_fields["display_number"]))
                    resp = ("msg_type:start_active_session_response\n"
                            "outcome:display in use\n")
                    break
            else:
                # No VNC process is running using the display we want to use.
                # However, check there is no leftover lock or pipe file.
                x_display_lock_file_path = "/tmp/.X{}-lock".format(msg_fields["display_number"])
                if os.path.exists(x_display_lock_file_path):
                    log.debug("Found X11 lock file @ {}".format(x_display_lock_file_path))
                    os.remove(x_display_lock_file_path)
                x_display_pipe_file_path = "/tmp/.X11-unix/X{}".format(msg_fields["display_number"])
                if os.path.exists(x_display_pipe_file_path):
                    log.debug("Found X11 pipe file @ {}".format(x_display_pipe_file_path))
                    os.remove(x_display_pipe_file_path)
                # Start a new VNC server
                log.debug("Creating VNC server for user: {}, disp: {}, name: {}, geo: {}, pf: {}".format(msg_fields["username"],
                                                                                                         msg_fields["display_number"],
                                                                                                         msg_fields["display_name"],
                                                                                                         msg_fields["geometry"],
                                                                                                         msg_fields["pixelformat"]))
                new_server = CreateNewVNCServer.CreateNewVNCServer("create_new_vnc_server",
                                                                   msg_fields["username"],
                                                                   msg_fields["display_number"],
                                                                   msg_fields["display_name"],
                                                                   msg_fields["geometry"],
                                                                   msg_fields["pixelformat"])
                new_server.start()
                resp = ("msg_type:start_active_session_response\n"
                        "outcome:success\n")
            # Send the response back to the caller
            sock.sendall(resp.encode('utf8'))

        elif msg_fields["msg_type"] == "kill_active_session":
            # Get the PID of the Xvnc process to kill from the message
            if "pid" in msg_fields:
                # Get a list of all the Xvnc processes running
                active_sessions = get_xvnc_process_info()
                # Confirm it is an Xvnc process that is active
                pid = msg_fields["pid"]
                for active_session in active_sessions:
                    if active_session["pid"] == pid:
                        # Kill it
                        os.kill(int(pid), signal.SIGKILL)
                        # Prepare response message to confirm the process was killed.
                        resp = ("msg_type:kill_active_session_response\n"
                                "outcome:killed\n")
                        break
                else:
                    # An Xvnc process with the requested PID was not found so
                    # nothing to kill (no work to do).
                    # Prepare response message for the client to explain this.
                    resp = ("msg_type:kill_active_session_response\n"
                            "outcome:process not found\n")
                # Send the response back to the caller
                sock.sendall(resp.encode('utf8'))

            else:
                msg = ("Invalid message from {0}:{1}."
                       " Missing PID value."
                       " Discarding".format(remote_addr[0],
                                            remote_addr[1]))
                log.warning(msg)


        else:
            # Discard message; not a "active_sessions_list" message
            msg = ("Invalid message from {0}:{1}."
                   " Invalid msg_type value."
                   " Discarding".format(remote_addr[0],
                                        remote_addr[1]))
            log.warning(msg)
    else:
        # Discard message; no msg_type field found.
        msg = ("Invalid message from {0}:{1}."
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