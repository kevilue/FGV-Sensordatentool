# Purpose

This program can be used to concatenate excel files containing the data collected from temperature sensors. The purpose of this project specifically is to use the data of temperature sensors, which are placed in different positions of water bodies for tracking purposes.

# Configuration

The files [settings.toml](settings.toml) and [sensors.toml](sensors.toml) serve as basic configuration for the application. The settings file contains comments for explanations. In the sensors file the available sensors are defined with a corresponding location of the sensor, which is added to the final library. It is important to define all sensors to be used in there, because finding an undefined sensor in the data will trigger an error. This is to avoid unwanted anomalies in the final data.

# Attributions

Application icon: \
[Thermometer icons created by apien - Flaticon](https://www.flaticon.com/free-icons/thermometer)
