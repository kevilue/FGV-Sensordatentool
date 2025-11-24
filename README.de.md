### Sprache

[![de](https://img.shields.io/badge/lang-de-red.svg)](./README.de.md)
[![en](https://img.shields.io/badge/lang-en-blue.svg)](./README.md)

# Nutzen

Dieses Tool wird vom [Fischerei- und Gewässerschutzverein Steinheim e.V.](https://fgv-steinheim.de/fgv/) (FGV) genutzt, um die Daten von Wassertemperatursensoren zusammengeführt in Microsoft PowerBI visualisieren zu können.

# Installation

> [!WARNING]
> Die .toml-Dateien müssen sich im selben Ordner wie die .exe Datei befinden, damit die Anwendung korrekt funktioniert.

## zip
Die .zip-Datei von den Releases herunterladen, extrahieren und die .exe starten.

## Installer
Die Installer .exe-Datei von den Releases herunterladen, und über den Setup-Assistenten installieren. Hier sollte sich der Installationspfad gemerkt werden, um später die Einstellungen und Sensoren anpassen zu können.

# Verwendung

Mit dieser kleinen Benutzeroberfläche können Microsoft Excel Dateien eingelesen werden, die Messdaten eines Temperatursensors enthalten. Diese werden zu einer großen csv-Datei kombiniert, die alle Daten enthält. Dabei müssen die Dateien drei Spalten enthalten; eine für die Temperatur, eine für den Zeitstempel und eine Index-Spalte. Die Namen der Spalten sowie sonstige Einstellungen können in der Datei [settings.toml](./settings.toml) erfolgen. Die Dateien mit den Sensordaten müssen den Sensornamen enthalten, das Suchmuster kann in Form eines regex-Ausdrucks ebenfalls in dieser Datei angepasst werden. Beim Einlesen der Sensordaten wird [sensors.toml](./sensors.toml) zum Abgleich der Namen verwendet, hier sollten also alle Sensoren die eingelesen werden sollen mit ihrem dazugehörigen Standort definiert sein. Dieser wird in der Ausgabedatei zu den Daten hinzugefügt.

# Referenzen / Quellen

Icon der Anwendung: \
[Thermometer icons created by apien - Flaticon](https://www.flaticon.com/free-icons/thermometer)