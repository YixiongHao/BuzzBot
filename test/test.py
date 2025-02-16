import os
import importlib.util

root = f"{os.path.dirname(os.path.abspath(__file__))}/.."
spec = importlib.util.spec_from_file_location("CONFIG", f"{root}/CONFIG.py")
CONFIG = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CONFIG)


print(CONFIG.INDEX_NAME)