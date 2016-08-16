import sys
import string
import socket
import errno
import select
import threading
import logging
import logging.handlers

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
    :return:
    """

    # :TODO: Should this be a separate file like the other tasks?

    # Configure logging
    log = logging.getLogger("{}".format(threading.current_thread().name))
    log.debug("Starting up...")

    # :TODO: Complete me!!!!

    # Read out the message data

    # Decode it

    # Determine what to do



if __name__ == "__main__":
    main()