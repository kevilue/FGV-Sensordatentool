import pandas as pd 
import time
import glob
import re

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
                self.log(f"An error occurred reading the file {file}:\n{e}")

        for df in dfs:
            df.dropna()

        self.log("Combining...")
        combined = pd.concat(dfs)
        combined[self.__config.timestamp] = pd.to_datetime(combined[self.__config.timestamp], format=self.__config.time_format)
        if self.__config.is_sorting_active: 
            self.log("Sorting...")
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

    def concat_sensor_files(self, path_to_files: str, save_path=None) -> None | pd.DataFrame :
        """Concatenate all given csv files collected from sensors into new ones."""
        data_paths = glob.glob(path_to_files+"\\FGV_*.xlsx", recursive=True)
        self.log("Found", len(data_paths), "files")

        sensors_chunks = {key: [] for key in self.__config.sensors.keys()}

        for idx, file in enumerate(data_paths):
            sensor_name = re.search(r"FGV_\d+", file).group()
            if not sensor_name in self.__config.sensors.keys():
                raise(NameError(f"Trying to read sensor {sensor_name} which is not defined in sensors.toml"))
            df = pd.read_excel(file)

            idxcol, timecol, tmpcol = None, None, None
            for idx, col in enumerate(df.columns):
                if self.__config.index in col:
                    idxcol = col
                elif self.__config.timestamp in col:
                    timecol = col
                elif self.__config.temperature in col:
                    tmpcol = col
                else: raise(IndexError(f"Found unknown column: {col}"))

            df[timecol] = pd.to_datetime(df[timecol], format=self.__config.time_format)
            df.sort_values(timecol, ascending=False, inplace=True)
            df.dropna()
            df = self.__transformSensorFile({"df": df, "idxcol": idxcol, "timecol": timecol, "tmpcol": tmpcol}, sensor_name, datetime_col=True)["df"]
            sensors_chunks[sensor_name].append(df)

        # Use topmost entry
        searchfunc = lambda x: x["Datum"].iloc[0]
        # Sort chunks after newest newest entry
        for key in sensors_chunks.keys():
            sensors_chunks[key].sort(key=searchfunc, reverse=True) # Newest at top
            sensors_chunks[key] = pd.concat(sensors_chunks[key])

        all_sensors_chunks = [sensors_chunks[key] for key in sensors_chunks.keys()]
        all_sensors_chunks = pd.concat(all_sensors_chunks)

        if save_path is not None:
            with open(save_path, "w") as f:
                all_sensors_chunks.to_csv(f, index=False)

        else: return all_sensors_chunks

    def append_sensor_files(self, path_to_files: str, save_path: str, old_file=None):
        """Concatenate an existing file with new ones."""
        stime = time.perf_counter()
        if old_file is not None:
            print("Reading old file...")
            base = pd.read_csv(old_file)
            print(f"Done ({time.perf_counter()-stime:.2f}s). Concatenating new files...")
            new = self.concat_sensor_files(path_to_files=path_to_files)
            print(f"Done ({time.perf_counter()-stime:.2f}s). Combining...")
            combined = pd.concat([new, base])
            print(f"Done ({time.perf_counter()-stime:.2f}s). Saving...")
            with open(save_path, "w") as f:
                combined.to_csv(f, index=False)
        else: 
            self.log("Concatenating files...")
            combined = self.concat_sensor_files(path_to_files=path_to_files, save_path=save_path)

        self.log(f"Done combining files, took {time.perf_counter()-stime:.2f}s")
        self.log("COMPLETED")

    def __transformSensorFile(df_dict: dict, sensor_name: str, datetime_col=False):
        """Split the three existing columns into eight with sensor info, location and separate columns for time data."""
        df_dict["df"].drop(df_dict["idxcol"], axis=1, inplace=True)
        if not datetime_col: df_dict["df"]["Datum"] = df_dict["df"][df_dict["timecol"]].dt.date
        else: df_dict["df"]["Datum"] = df_dict["df"][df_dict["timecol"]]
        df_dict["df"]["Jahr"] = df_dict["df"][df_dict["timecol"]].dt.year
        df_dict["df"]["Monat"] = df_dict["df"][df_dict["timecol"]].dt.month
        df_dict["df"]["Tag"] = df_dict["df"][df_dict["timecol"]].dt.day
        df_dict["df"]["Uhrzeit"] = df_dict["df"][df_dict["timecol"]].dt.time
        df_dict["df"]["Sensor"] = sensor_name
        df_dict["df"]["Standort"] = sensors[sensor_name]["location"]
        df_dict["df"].drop(df_dict["timecol"], axis=1, inplace=True)
        df_dict["df"].rename(columns={df_dict["tmpcol"]: "Temperatur"}, inplace=True)
        return df_dict