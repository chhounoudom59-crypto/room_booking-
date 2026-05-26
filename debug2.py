import sys
import traceback

try:
    pass
except Exception:
    for _tb in traceback.extract_tb(sys.exc_info()[2]):
        pass
