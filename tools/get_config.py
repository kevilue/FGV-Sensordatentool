import tomllib
import os
import sys

class AppConfig:
    __config = dict()

    def __init__(self, config_path, sensors_path):
        if not os.path.isfile(config_path):
            print("No config found, proceeding with default settings")
        if not os.path.isfile(sensors_path):
            print("No sensors config found - aborting.")
            sys.exit(1)
        try:
            with open(config_path, "rb") as f:
                self.__config = tomllib.load(f)
            with open(sensors_path, "rb") as f:
                self.__sensors = tomllib.load(f)
        except Exception as e:
            print("Error loading config file:", e)


    @property
    def sensors(self):
        if self.__sensors:
            return self.__sensors.keys()
        
    def sensor_loc(self, sensor):
        if self.__sensors:
            return self.__sensors[sensor]["location"]

    @property
    def timestamp(self):
        if self.__config["names"]["timestamp_column"]:
            return self.__config["names"]["timestamp_column"]
        else:
            return "timestamp"
        
    @property
    def index(self):
        if self.__config["names"]["index_column"]:
            return self.__config["names"]["index_column"]
        else:
            return "index"
        
    @property
    def temperature(self):
        if self.__config["names"]["temperature_column"]:
            return self.__config["names"]["temperature_column"]
        else:
            return "temperature"
        
    @property
    def time_format(self):
        if self.__config["formats"]["time_format"]:
            return self.__config["formats"]["time_format"]
        else:
            return "%Y-%m-%d %H:%M:%S"
        
    @property
    def sort_ascending_active(self):
        if self.__config["sorting"]["order"]:
            if self.__config["sorting"]["order"] == "ascending": return True
            else: return False
        return False
    
    def get_resource_path(self, relative_path):
        """ Get resource path for pyinstaller. """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)