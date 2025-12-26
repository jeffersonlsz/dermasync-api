from enum import Enum


class RelatoIntent(str, Enum):
    UPLOAD_FILES = "upload_files"
    START_PROCESSING = "start_processing"
    FAIL_RELATO = "fail_relato"
