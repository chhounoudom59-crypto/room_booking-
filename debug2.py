import sys
import traceback

try:
    pass
except Exception:
    for tb in traceback.extract_tb(sys.exc_info()[2]):
        print(f'File: {tb.filename}, Line: {tb.lineno}')
