import configparser

INIFile = "pySpeed.ini"
config = configparser.ConfigParser()

def read(key):
    config.read(INIFile)
    return config.get("DEFAULT", str(key), fallback="")
    
def write(**kwargs):
    for name, value in kwargs.items():
        config["DEFAULT"][name] = str(value)
    with open(INIFile, "w") as configfile:
        config.write(configfile)
    return 1
