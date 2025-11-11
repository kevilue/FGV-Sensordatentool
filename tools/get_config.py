import tomllib

class AppConfig:
    __config = dict()

    def __init__(self, path):
        try:
            with open(path, "rb") as f:
                self.__config = tomllib.load(f)
        except Exception as e:
            print("Error loading config file:", e)

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
    def is_sorting_active(self):
        if self.__config["sorting"]["enable"]:
            return True
        else:
            return False
        
    @property
    def sort_ascending_active(self):
        if self.__config["sorting"]["order"]:
            if self.__config["sorting"]["order"] == "ascending": return True
            else: return False
        return False