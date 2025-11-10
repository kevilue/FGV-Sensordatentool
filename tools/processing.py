import time

class DataHandler:
    def __init__(self, log_queue):
        self.log_queue = log_queue

    def log(self, msg):
        self.log_queue.put(msg)

    def simulate_process(self, duration):
        self.log("Starting process...")
        time.sleep(duration)
        self.log("Done.")
        self.log_queue.put("COMPLETED")
