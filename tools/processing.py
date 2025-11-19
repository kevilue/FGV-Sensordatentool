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

    def concat_sensor_files(
            self, 
            path_to_files: str | list[str], 
            save_path=None,
            sort=True,
            drop_duplicates=False
            ) -> None | pd.DataFrame :
        """Concatenate all given csv files collected from sensors into new ones."""
        if type(path_to_files) is list: 
            data_paths = path_to_files
        else:
            data_paths = glob.glob(path_to_files+"\\FGV_*.xlsx", recursive=True)
            self.log(f"{len(data_paths)} Datei(en) gefunden")

        sensors_chunks = {}
        
        for file in data_paths:
            try: sensor_name = re.search(r"FGV_\d+", file).group()
            except Exception as e:
                self.log(f"Fehler beim Lesen von {file}: {e}. Stellen Sie sicher, dass alle Dateien der neuen Sensordaten mit 'FGV_[sensorid]' beginnen.")
            if sensor_name not in sensors_chunks.keys():
                sensors_chunks[sensor_name] = []
            if not sensor_name in self.__config.sensors:
                raise(NameError(f"Versuche Sensor {sensor_name} zu lesen der nicht in sensors.toml definiert wurde. Bitte fügen Sie den neuen Sensor hinzu."))
            else: self.log(f"Lese Daten für Sensor {sensor_name}")
            df = pd.read_excel(file)

            idxcol, timecol, tmpcol = None, None, None
            for col in df.columns:
                if self.__config.index in col:
                    idxcol = col
                elif self.__config.timestamp in col:
                    timecol = col
                elif self.__config.temperature in col:
                    tmpcol = col
                else: raise(IndexError(f"Nicht bekannte Spalte in Daten gefunden: {col}"))

            if sort and save_path is not None:
                df[timecol] = pd.to_datetime(df[timecol], format=self.__config.time_format)
                df.sort_values(timecol, ascending=self.__config.sort_ascending_active, inplace=True)
            df.dropna()
            if drop_duplicates: df.drop_duplicates(inplace=True)
            df = self.__transformSensorFile({"df": df, "idxcol": idxcol, "timecol": timecol, "tmpcol": tmpcol}, sensor_name, datetime_col=True)["df"]
            sensors_chunks[sensor_name].append(df)

        if save_path is not None: self.log("Kombiniere...")

        # Use topmost entry
        searchfunc = lambda x: x["Datum"].iloc[0]

        for key in sensors_chunks.keys():
            if sort and save_path is not None: 
                # Sort chunks after newest newest entry
                sensors_chunks[key].sort(key=searchfunc, reverse=not self.__config.sort_ascending_active) # Newest at top
            sensors_chunks[key] = pd.concat(sensors_chunks[key])

        all_sensors_chunks = [sensors_chunks[key] for key in sensors_chunks.keys()]
        all_sensors_chunks = pd.concat(all_sensors_chunks)

        if save_path is not None:
            self.log("Fertig. Speichern...")
            with open(save_path, "w") as f:
                all_sensors_chunks.to_csv(f, index=False)

        else: return all_sensors_chunks

    def append_sensor_files(
            self, 
            path_to_files: str | list[str] | None, 
            save_path: str, 
            old_file=None,
            sort=True,
            drop_duplicates=True
            ):
        """Concatenate an existing file (old_file, optional) with new ones and save under save_path."""
        stime = time.perf_counter()
        if old_file is not None:
            self.log("Lese existierende Bibliothek...")
            base = pd.read_csv(old_file)
            if path_to_files is not None:
                self.log(f"Fertig ({time.perf_counter()-stime:.2f}s). Kombiniere neue Dateien...")
                new = self.concat_sensor_files(path_to_files=path_to_files)
                self.log(f"Fertig ({time.perf_counter()-stime:.2f}s). Kombiniere...")
                base = pd.concat([new, base])
            if drop_duplicates:
                self.log("Eliminiere Duplikate...")
                base.dropna(inplace=True)
                base.drop_duplicates(inplace=True)
            if sort:
                self.log("Sortiere...")
                base["Datum"] = pd.to_datetime(base["Datum"], format=self.__config.time_format)
                base_sorted = base.sort_values(by=["Sensor", "Datum"], ascending=[True, self.__config.sort_ascending_active])
                base = base_sorted
            self.log(f"Fertig ({time.perf_counter()-stime:.2f}s). Speichern...")
            with open(save_path, "w") as f:
                base.to_csv(f, index=False)
        else: 
            self.log("Kombiniere Dateien...")
            self.concat_sensor_files(path_to_files=path_to_files, save_path=save_path, sort=sort, drop_duplicates=drop_duplicates)

        self.log(f"Verarbeitung fertig. Dauer: {time.perf_counter()-stime:.2f}s")
        self.log("CONCAT_COMPLETED")

    def __transformSensorFile(self, df_dict: dict, sensor_name: str, datetime_col=False):
        """Split the three existing columns into eight with sensor info, location and separate columns for time data."""
        df_dict["df"].drop(df_dict["idxcol"], axis=1, inplace=True)
        if not datetime_col: df_dict["df"]["Datum"] = df_dict["df"][df_dict["timecol"]].dt.date
        else: df_dict["df"]["Datum"] = df_dict["df"][df_dict["timecol"]]
        df_dict["df"]["Jahr"] = df_dict["df"][df_dict["timecol"]].dt.year
        df_dict["df"]["Monat"] = df_dict["df"][df_dict["timecol"]].dt.month
        df_dict["df"]["Tag"] = df_dict["df"][df_dict["timecol"]].dt.day
        df_dict["df"]["Uhrzeit"] = df_dict["df"][df_dict["timecol"]].dt.time
        df_dict["df"]["Sensor"] = sensor_name
        df_dict["df"]["Standort"] = self.__config.sensor_loc(sensor_name)
        df_dict["df"].drop(df_dict["timecol"], axis=1, inplace=True)
        df_dict["df"].rename(columns={df_dict["tmpcol"]: "Temperatur"}, inplace=True)
        return df_dict
    
    def get_newest_sensor_entries(self, path_to_file: str):
        """Read the given csv file and return latest entries for unique sensors."""
        with open(path_to_file, "r") as f:
            df = pd.read_csv(f)

        sensors = df["Sensor"].unique()
        self.log(f"{len(sensors)} Sensor(en) in der Datei gefunden")

        results = []
        for sensor in sensors:
            sensor_time_min = df.query("Sensor == @sensor")["Datum"].max()
            results.append({"name": sensor, "latest": sensor_time_min})

        return results