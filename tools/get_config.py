import tomllib
import os
import sys
import gettext

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

        try: lang = gettext.translation("base", localedir=self.get_resource_path("locales"), languages=[self.language], fallback=True)
        except Exception as e: 
            print(f"Error getting translations for {self.language}:",e)
            pass
        lang.install()


    @property
    def sensors(self):
        if self.__sensors:
            return self.__sensors.keys()
        
    def sensor_loc(self, sensor) -> str:
        if self.__sensors:
            return self.__sensors[sensor]["location"]

    @property
    def timestamp(self) -> str:
        return self.__config.get("names",{}).get("timestamp_column", "timestamp")
        
    @property
    def index(self) -> str:
        return self.__config.get("names",{}).get("index_column", "index")
        
    @property
    def temperature(self) -> str:
        return self.__config.get("names",{}).get("temperature_column", "temperature")
        
    @property
    def time_format(self) -> str:
        return self.__config.get("formats",{}).get("time_format", "%Y-%m-%d %H:%M:%S")
        
    @property
    def sort_ascending_active(self) -> bool:
        order = self.__config.get("sorting",{}).get("order")
        if order == "ascending":
            return True
        elif order == "descending": 
            return False
        else:
            return False
    
    @property
    def file_search_pattern(self) -> str:
        return self.__config.get("names",{}).get("sensor_filename_pattern", "FGV_*.xlsx")
    
    @property
    def sensor_name_pattern(self) -> str:
        return self.__config.get("names",{}).get("sensor_name_pattern", r"FGV_\d+")
        
    @property
    def language(self) -> str:
        return self.__config.get("language",{}).get("lang", "en")
        
    @property
    def decimal_points(self) -> int:
        return self.__config.get("formats",{}).get("decimal_points", 2)

    def get_resource_path(self, relative_path) -> str:
        """ Get resource path for pyinstaller. """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)