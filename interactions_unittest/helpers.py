""" Helper functions for the interactions unit tests. """
import datetime
from os import urandom

def random_snowflake() -> int:
    """ Generate a random snowflake. """
    timestamp = int(
        (datetime.datetime.now() - datetime.datetime(2015, 1, 1)).total_seconds() * 1000
    )
    worker = int(f"0x{urandom(5).hex()}", 0)
    process = int(f"0x{urandom(5).hex()}", 0)
    increment = int(f"0x{urandom(12).hex()}", 0)

    return int((timestamp << 22) | (worker << 17) | (process << 12) | increment)
