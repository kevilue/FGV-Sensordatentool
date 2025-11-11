import gui
from tools.get_config import AppConfig

if __name__ == "__main__":
    conf = AppConfig("settings.toml")
    app = gui.MainApp(conf)
    app.mainloop()