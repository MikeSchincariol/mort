import multiprocessing as mp
import time

def parent():
    print("Parent: Started")
    while True:
        print("Parent: Tick")
        time.sleep(1)
    print("Parent: Exiting")


def child():
    print("Child: Started")
    while True:
        print("Child: Tick")
        time.sleep(1)
    print("Child: Exiting")

if __name__ == "__main__":
    daemon = mp.Process(target=parent,
                        name="TestDaemon",
                        daemon=True)

    daemon.start()
    print("Daemon started with PID: {}".format(daemon.pid))
