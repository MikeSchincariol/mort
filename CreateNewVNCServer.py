#!/usr/bin/env python3

import sys
import os
import os.path
import pwd
import subprocess
import multiprocessing
import logging
import time

class CreateNewVNCServer(multiprocessing.Process):

    def __init__(self, name, username, display_number, display_name, geometry, pixelformat):
        super().__init__(name=name)

        log = logging.getLogger("CreateNewVNCServer")
        log.debug("Starting up....")

        self.username = username
        self.display_number = display_number
        self.display_name = display_name
        self.geometry = geometry
        self.pixelformat = pixelformat


    def run(self):
        """
        Starts a new VNC server process as a given user.
        """
        # Get a new logger to use
        log = logging.getLogger("CreateNewVNCServer")
        log.info("Creating a VNC server for {}".format(self.username))

        # Get the current environment and modify it to represent the new user
        new_env = os.environ.copy()
        new_env["USER"] = self.username
        new_env["LOGNAME"] = self.username
        new_env["HOME"] = pwd.getpwnam(self.username).pw_dir
        new_env["CWD"] = pwd.getpwnam(self.username).pw_dir

        # Change to user
        gid = pwd.getpwnam(self.username).pw_gid
        os.setgid(gid)
        uid = pwd.getpwnam(self.username).pw_uid
        os.setuid(uid)
        os.chdir(pwd.getpwnam(self.username).pw_dir)

        # Build up the args to use in the call to vncserver
        args = []
        args.append("vncserver")
        args.append(":{}".format(self.display_number))

        if self.display_name is None or self.display_name == "":
            # Use default display name created by vncserver
            pass
        else:
            args.append("-name")
            args.append(self.display_name)

        if self.geometry is None or self.geometry == "":
            # Use default geometry selected by vncserver
            pass
        else:
            args.append("-geometry")
            args.append(self.geometry)

        if self.pixelformat is None or self.pixelformat == "":
            # Use default pixelformat based on depth
            pass
        else:
            args.append("-pixelformat")
            args.append(self.pixelformat)


        # Kick off the VNC server
        subprocess.Popen(args, env=new_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    p = CreateNewVNCServer("create_new_vnc_server",
                           "mike",
                           "129",
                           "Mikes Test VNC Session",
                           "1280x720",
                           "RGB888")
    p.start()
