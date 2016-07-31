import multiprocessing as mp
import subprocess
import os
import time
import signal


class MortTask(mp.Process):

    def __init__(self, name):
        super().__init__(name=name)

        print("MortTask[{}:{}] Initializing...".format(self.name, self.pid))
        self.task_exit = False

        # Connect up signal handlers
        signal.signal(signal.SIGHUP, self.task_sig_handler)
        signal.signal(signal.SIGQUIT, self.task_sig_handler)
        signal.signal(signal.SIGABRT, self.task_sig_handler)
        signal.signal(signal.SIGUSR1, self.task_sig_handler)
        signal.signal(signal.SIGUSR2, self.task_sig_handler)
        signal.signal(signal.SIGTERM, self.task_sig_handler)


    def run(self):
        print("MortTask[{}:{}]: Started".format(self.name, self.pid))
        subprocess.call(["vncserver", ":100"])
        while True:
            print("MortTask[{}:{}]: Tick".format(self.name, self.pid))
            time.sleep(2)
            if self.task_exit:
                break


    def task_sig_handler(self, signal_caught, frame):
        signal_list = {1: "SIGHUP",
                       3: "SIGQUIT",
                       6: "SIGABRT",
                       10: "SIGUSR1",
                       12: "SIGUSR2",
                       15: "SIGTERM"}

        print("MortTask[{}:{}]: Caught: {}".format(self.name, self.pid, signal_list[signal_caught]))
        self.task_exit = True




class MortDaemon(mp.Process):

    def __init__(self, name):
        super().__init__(name=name)

        print("MortDaemon[{}:{}] Initializing...".format(self.name, self.pid))
        self.daemon_exit = False
        self.task_count = 0

        # Connect up signal handlers
        signal.signal(signal.SIGHUP, self.daemon_sig_handler)
        signal.signal(signal.SIGQUIT, self.daemon_sig_handler)
        signal.signal(signal.SIGABRT, self.daemon_sig_handler)
        signal.signal(signal.SIGUSR1, self.daemon_sig_handler)
        signal.signal(signal.SIGUSR2, self.daemon_sig_handler)
        signal.signal(signal.SIGTERM, self.daemon_sig_handler)


    def run(self):
        print("MortDaemon[{}:{}]: Started".format(self.name, self.pid))
        while True:
            print("MortDaemon[{}:{}]: Tick".format(self.name, self.pid))
            time.sleep(2)
            if self.daemon_exit:
                break

        print("MortDaemon[{}:{}] Exiting".format(self.name, self.pid))



    def daemon_sig_handler(self, signal_caught, frame):
        signal_list = {1:  "SIGHUP",
                       3:  "SIGQUIT",
                       6:  "SIGABRT",
                       10: "SIGUSR1",
                       12: "SIGUSR2",
                       15: "SIGTERM"}

        print("MortDaemon[{}:{}]: Caught: {}".format(self.name, self.pid, signal_list[signal_caught]))

        if signal_caught == signal.SIGUSR1:
            print("MortDaemon[{}:{}]: Starting VNC server".format(self.name, self.pid))
            p = MortTask("task{}".format(self.task_count))
            p.start()
            self.task_count += 1
            print("MortDaemon[{}:{}]: VNC server started with PID: {}".format(self.name, self.pid, p.pid))
        else:
            self.daemon_exit = True




if __name__ == "__main__":
    mp.set_start_method("fork")
    p = MortDaemon(name="toplevel")
    p.start()
