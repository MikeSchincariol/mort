import sys
import socket
import errno
import select
import logging
import logging.handlers

import ServerAnnounceTask


# Configure a log file, to write log messages into, that auto-rotates when
# it reaches a certain size.
rotating_log_handler = logging.handlers.RotatingFileHandler(filename='mort_session_server.log',
                                                   mode='a',
                                                   maxBytes=1E6,
                                                   backupCount=3)
logging.basicConfig(format="{asctime} :{levelname}: {name}({lineno}) - {message}",
                    style="{",
                    level=logging.DEBUG,
                    handlers=[rotating_log_handler])
log = logging.getLogger("mort_session_server")

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
            log.info("Opened socket at TCP:{0}".format(my_port))
            break
        except OSError as ex:
            if ex.errno == errno.EADDRINUSE:
                my_port += 1
            else:
                raise
    else:
        log.critical("Could not find an open port in the range 42124 to 59999.")
        log.critical("Session server exiting.")
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
announce_task.join()
conn, remote_addr = sock.accept()
log.info("Accepted connection from: {}".format(remote_addr))
while True:
    # Get the request datagram
    robj, wobj, xobj = select.select([conn], [], [])

    # Determine what to do


    # Do it...


    # Send respose back



# How do shut down?
#    Need to implement signal handling logic....
