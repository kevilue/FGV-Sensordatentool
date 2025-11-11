import pandas as pd 
import time

class DataHandler:
    def __init__(self, log_queue, config):
        self.log_queue = log_queue
        self.__config = config

    def log(self, msg):
        self.log_queue.put(msg)

    def simulate_process(self, duration):
        self.log("Starting process...")
        time.sleep(duration)
        self.log("Done.")
        self.log_queue.put("COMPLETED")

    def concatenate_csv_files(self, fpaths: list[str], savepath):
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
        combined[self.__config.timestamp] = pd.to_datetime(combined[self.__config.timestamp], format=self.__config.time_format)
        if self.__config.is_sorting_active: 
            combined.sort_values(by=self.__config.timestamp, ascending=self.__config.sort_ascending_active, inplace=True)

        combined.to_csv(savepath, index=False)
        etime = time.perf_counter()
        self.log(f"Done in {(etime-stime)*1000:.2f}ms. File saved to {savepath}.")
        self.log("COMPLETED")

    def resample_csv_file(
            self, 
            path: str, 
            savepath, 
            sample_dist="20min", 
            # time_format="%Y-%m-%d %H:%M:%S",
            start=None,
            end=None
    ):
        self.log("Reading file")
        stime = time.perf_counter()
        sourcefile = pd.read_csv(path)
        sourcefile[self.__config.timestamp] = pd.to_datetime(sourcefile[self.__config.timestamp], format=self.__config.time_format)
        # Trim
        if start is not None:
            sourcefile = sourcefile.query(f"@start <= {self.__config.timestamp}")
        if end is not None:
            sourcefile = sourcefile.query(f"{self.__config.timestamp} <= @end")
        # Resample
        self.log("Resampling...")
        sourcefile = sourcefile.set_index(self.__config.timestamp)
        resampled_sourcefile = sourcefile.resample(sample_dist).mean()
        resampled_sourcefile = resampled_sourcefile.reset_index()
        # Drop index column (resampling created float values)
        resampled_sourcefile = resampled_sourcefile.drop("index", axis=1)
        self.log("Saving...")
        with open(savepath, "w", encoding="utf-8") as f:
            resampled_sourcefile.to_csv(f, index_label="index") # Re-add index column
        etime = time.perf_counter()
        self.log(f"Finished in {(etime-stime)*1000:.2f}ms.")
        self.log("COMPLETED")