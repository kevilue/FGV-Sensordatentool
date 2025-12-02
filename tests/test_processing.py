import pytest
import queue
import glob
import pandas as pd
import os
from tools.processing import DataHandler
from tools.get_config import AppConfig

class TestProcessing:

    def __getHandler(self, gc=False):
        config = AppConfig("settings.toml", "sensors.toml")
        q = queue.Queue()
        handler = DataHandler(q, config)
        if gc: return handler, config
        else: return handler

    def test_newest_sensor_entries(self):
        """test if function actually returns the latest sensor entries"""
        handler = self.__getHandler()
        res = handler.get_newest_sensor_entries("./test/test_data/basic_lib_dummy.csv")
        assert res[0] == {
            "name": "FGV_01",
            "latest": "2025-02-12 15:50:00"
        }
        assert res[1] == {
            "name": "FGV_02",
            "latest": "2025-02-12 15:20:00"
        }

    def test_concat_new_only(self):
        """test if only concatenating new sensor data files works correctly and formatting matches"""
        handler, cfg = self.__getHandler(gc=True)
        filepaths = glob.glob("./test/test_data/FGV_*_sensor_data_dummy_[0-9].xlsx", recursive=True)
        handler.concat_sensor_files(
            path_to_files=filepaths,
            save_path="./test/test_data/temp.csv",
            round_temperatures=True
        )
        with open("./test/test_data/temp.csv", "r") as f:
            res = pd.read_csv(f)
        res["Datum"] = pd.to_datetime(res["Datum"], format=cfg.time_format)
        # Check if time columns got extracted correctly
        assert (res["Datum"].dt.year == res["Jahr"]).all()
        assert (res["Datum"].dt.day == res["Tag"]).all()
        res["Uhrzeit"] = pd.to_datetime(res["Uhrzeit"], format=cfg.time_format.split(" ")[-1]).dt.time # Assumes date and time is separated by space
        assert (res["Datum"].dt.time == res["Uhrzeit"]).all()
        # Check if number of decimal points matches settings
        assert len(str(res.iloc[0]["Temperatur"]).split(".")[-1]) == cfg.decimal_points
        # Check if default active descending sorting worked for all sensors
        sensors = res["Sensor"].unique()
        for sensor in sensors:
            sensor_timestamps = res.query("Sensor == @sensor")["Datum"] # Get timestamps
            assert sensor_timestamps.is_monotonic_decreasing
        os.remove("./test/test_data/temp.csv") # Delete temporary result file
        
    def test_bad_sensor_filename(self):
        """test if sensor file with unknown sensor name results in NameError"""
        handler = self.__getHandler()
        filepaths = ["./test/test_data/FGV_00_bad_sensor.xlsx"]
        with pytest.raises(NameError):
                handler.append_sensor_files(
                path_to_files=filepaths,
                save_path="./test/test_data/temp.csv",
            )
                
    def test_bad_sensor_column(self):
        """test if sensor data with unknown column name results in IndexError"""
        handler = self.__getHandler()
        filepaths = ["./test/test_data/FGV_01_bad_sensor_col.xlsx"]
        with pytest.raises(IndexError):
            handler.append_sensor_files(
            path_to_files=filepaths,
            save_path="./test/test_data/temp.csv",
            )

    def test_sorting_disabled(self):
        """test if disabling sorting actually results in unsorted results"""
        handler, cfg = self.__getHandler(gc=True)
        # Get shuffled test data
        filepaths = glob.glob("./test/test_data/FGV_*_sensor_data_dummy_*_shuffled.xlsx", recursive=True)
        handler.concat_sensor_files(
            path_to_files=filepaths,
            save_path="./test/test_data/temp.csv",
            sort=False
        )
        with open("./test/test_data/temp.csv", "r") as f:
            res = pd.read_csv(f)
        res["Datum"] = pd.to_datetime(res["Datum"], format=cfg.time_format)
        sensors = res["Sensor"].unique()
        for sensor in sensors:
            sensor_timestamps = res.query("Sensor == @sensor")["Datum"] # Get timestamps
            assert not sensor_timestamps.is_monotonic_decreasing
        os.remove("./test/test_data/temp.csv") # Delete temporary result file
    
    def test_sorting_enabled(self):
        """test if enabling sorting actually results in sorted results"""
        handler, cfg = self.__getHandler(gc=True)
        # Get shuffled test data
        filepaths = glob.glob("./test/test_data/FGV_*_sensor_data_dummy_*_shuffled.xlsx", recursive=True)
        handler.concat_sensor_files(
            path_to_files=filepaths,
            save_path="./test/test_data/temp.csv",
            sort=True
        )
        with open("./test/test_data/temp.csv", "r") as f:
            res = pd.read_csv(f)
        res["Datum"] = pd.to_datetime(res["Datum"], format=cfg.time_format)
        sensors = res["Sensor"].unique()
        for sensor in sensors:
            sensor_timestamps = res.query("Sensor == @sensor")["Datum"] # Get timestamps
            assert sensor_timestamps.is_monotonic_decreasing
        os.remove("./test/test_data/temp.csv") # Delete temporary result file

    def test_remove_duplicates_enabled(self):
        """test if removing duplicates works"""
        handler = self.__getHandler()
        # Get test data with duplicate rows
        filepaths = glob.glob("./test/test_data/FGV_*_sensor_data_duplicate_rows_*.xlsx", recursive=True)
        total_entries = 0
        # Get amount of rows including duplicates
        for f in filepaths:
            with open(f, "rb") as file:
                df = pd.read_excel(file)
                total_entries += df.shape[0]
        handler.concat_sensor_files(
        path_to_files=filepaths,
        save_path="./test/test_data/temp.csv",
        drop_duplicates=True
        )
        with open("./test/test_data/temp.csv", "r") as f:
            res = pd.read_csv(f)
        assert res.shape[0] < total_entries # Combined file should have less rows
        os.remove("./test/test_data/temp.csv") # Delete temporary result file

    def test_append_sensor_files_onlyold(self):
        """test only modifying an existing data library with the DataHandler.append_sensor_files function"""
        handler, cfg = self.__getHandler(gc=True)
        # Test existing library only
        libp = "./test/test_data/basic_lib_dummy_shuffled.csv"
        handler.append_sensor_files(
            path_to_files=None,
            old_file=libp,
            sort=True,
            save_path="./test/test_data/temp.csv"
        )
        with open("./test/test_data/temp.csv", "r") as f:
            res = pd.read_csv(f)
        res["Datum"] = pd.to_datetime(res["Datum"], format=cfg.time_format)
        # Test if sorting worked for verification
        sensors = res["Sensor"].unique()
        for sensor in sensors:
            sensor_timestamps = res.query("Sensor == @sensor")["Datum"] # Get timestamps
            assert sensor_timestamps.is_monotonic_decreasing
        # Test if amount of rows matches
        with open(libp, "r") as f:
            cmp = pd.read_csv(f)
            total_entries = cmp.shape[0]
        assert res.shape[0] == total_entries
        os.remove("./test/test_data/temp.csv") # Delete temporary result file

    def test_append_sensor_files_newonly(self):
        """test only concatenating new files with the DataHandler.append_sensor_files function"""
        handler, cfg = self.__getHandler(gc=True)
        # Use shuffled data to check for sorting
        filepaths = glob.glob("./test/test_data/FGV_*_sensor_data_dummy_*_shuffled.xlsx", recursive=True)
        handler.append_sensor_files(
            path_to_files=filepaths,
            save_path="./test/test_data/temp.csv"
        )
        total_entries = 0
        for f in filepaths:
            with open(f, "rb") as file:
                df = pd.read_excel(f)
                total_entries += df.shape[0]
        with open("./test/test_data/temp.csv", "r") as f:
            res = pd.read_csv(f)
        res["Datum"] = pd.to_datetime(res["Datum"], format=cfg.time_format)
        sensors = res["Sensor"].unique()
        assert res.shape[0] == total_entries # Amount of entries should match
        for sensor in sensors: # Check if sorting worked
            sensor_timestamps = res.query("Sensor == @sensor")["Datum"] # Get timestamps
            assert sensor_timestamps.is_monotonic_decreasing
        os.remove("./test/test_data/temp.csv")

    def test_concat_existing_lib(self):
        """test if combining an existing data library with new sensor files results in file of correct length"""
        handler = self.__getHandler()
        filepaths = glob.glob("./test/test_data/FGV_*_sensor_data_dummy_[0-9].xlsx", recursive=True)
        libpath = "./test/test_data/basic_lib_dummy.csv"
        # Get total amount of entries to combine
        total_entries = 0
        for f in filepaths:
            with open(f, "rb") as file:
                df = pd.read_excel(f)
                total_entries += df.shape[0]
        with open(libpath, "r") as f:
            df = pd.read_csv(f)
            total_entries += df.shape[0]
        # Combine
        handler.append_sensor_files(
            path_to_files=filepaths,
            save_path="./test/test_data/temp.csv",
            old_file=libpath,
            drop_duplicates=False
        )
        # Check result
        with open("./test/test_data/temp.csv", "r") as f:
            res = pd.read_csv(f)
        assert res.shape[0] == total_entries
        os.remove("./test/test_data/temp.csv") # Delete temporary result file
