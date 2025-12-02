import pytest
import gettext
import tomllib
from tools.get_config import AppConfig
import os 

class TestConfig:
    
    def test_no_sensorfile(self):
        """config class without sensors file should result in sys.exit(1)"""
        with pytest.raises(SystemExit) as e:
            config = AppConfig("", "")
        assert e.type == SystemExit
        assert e.value.code == 1

    def test_default_settings(self):
        """test default settings if no config file is present"""
        config = AppConfig("", "sensors.toml")
        assert config.timestamp == "timestamp"
        assert config.index == "index"
        assert config.temperature == "temperature"
        assert config.time_format == "%Y-%m-%d %H:%M:%S"
        assert config.sort_ascending_active == False
        assert config.file_search_pattern == "FGV_*.xlsx"
        assert config.sensor_name_pattern == r"FGV_\d+"
        assert config.language == "en"
        assert config.decimal_points == 2

    def test_settings_available(self):
        """test if the available settings get passed correctly"""
        with open("settings.toml", "rb") as f:
            config = tomllib.load(f)
        appconfig = AppConfig("settings.toml", "sensors.toml")
        assert config["names"]["timestamp_column"] == appconfig.timestamp
        assert config["names"]["index_column"] == appconfig.index
        assert config["names"]["temperature_column"] == appconfig.temperature
        assert config["names"]["sensor_filename_pattern"] == appconfig.file_search_pattern
        assert config["names"]["sensor_name_pattern"] == appconfig.sensor_name_pattern
        assert config["language"]["lang"] == appconfig.language
        assert config["formats"]["time_format"] == appconfig.time_format
        assert config["formats"]["decimal_points"] == appconfig.decimal_points
        # Sorting order
        order = config.get("sorting",{}).get("order")
        if order == "ascending": order = True
        elif order == "descending": order = False
        assert order == appconfig.sort_ascending_active
        
    def test_locales_available(self):
        """check if locales folder for translations is available and usable"""
        config = AppConfig("settings.toml", "sensors.toml")
        lang = gettext.translation("base", localedir=config.get_resource_path("locales"), languages=["en"], fallback=True)
        assert type(lang) == gettext.GNUTranslations

    def test_get_resource_path(self):
        """
        test if correct resource path is returned when running with normal python interpreter
        when running in compiled .exe the path returns the absolute path to sys._MEIPASS + the relative path
        """
        config = AppConfig("settings.toml", "sensors.toml")
        actualpath = os.path.abspath(".")
        actualpath = os.path.join(actualpath, "test")
        assert actualpath == config.get_resource_path("test")