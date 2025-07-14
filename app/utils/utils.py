# app/utils/utils.py

import inspect


def log_location():
    frame = inspect.currentframe().f_back
    filename = frame.f_code.co_filename
    methodname = frame.f_code.co_name
    lineno = frame.f_lineno
    return f"{filename}:{methodname}:{lineno}"