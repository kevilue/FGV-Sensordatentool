import pandas as pd 
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

    def concatenate_csv_files(self, fpaths: list[str], savepath, time_format="%Y-%m-%d %H:%M:%S"):
        """
        Concatenate given csv files. Newest timestamps are put at the top,
        and the whole file will be sorted.
        """
        stime = time.perf_counter()
        self.log(f"Reading {len(fpaths)} files...")

        dfs = []
        for file in fpaths:
            try:
                dfs.append(pd.read_csv(file))
            except Exception as e:
                self.log(f"An error occured reading the file {file}:\n{e}")

        for df in dfs:
            df.dropna()

        self.log("Combining and sorting...")
        combined = pd.concat(dfs)
        combined["timestamp"] = pd.to_datetime(combined["timestamp"], format=time_format)
        combined.sort_values(by="timestamp", ascending=False, inplace=True)

        combined.to_csv(savepath, index=False)
        etime = time.perf_counter()
        self.log(f"Done in {(etime-stime)*1000:.2f}ms. File saved to {savepath}.")
        self.log("COMPLETED")