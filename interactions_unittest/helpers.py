"""Helper functions for the interactions unit tests."""

import datetime
from os import urandom
import typing

import interactions


def random_snowflake() -> int:
    """Generate a random snowflake."""
    timestamp = int(
        (datetime.datetime.now() - datetime.datetime(2015, 1, 1)).total_seconds() * 1000
    )
    worker = int(f"0x{urandom(5).hex()}", 0)
    process = int(f"0x{urandom(5).hex()}", 0)
    increment = int(f"0x{urandom(12).hex()}", 0)

    return int((timestamp << 22) | (worker << 17) | (process << 12) | increment)


def fake_process_files(files, file=None):
    """Process the files (raise exception if any attachment is used)."""
    has_files = bool(files or file)
    is_attachment = (
        isinstance(file, interactions.models.discord.message.Attachment)
        or isinstance(files, interactions.models.discord.message.Attachment)
        or (
            isinstance(files, typing.Iterable)
            and any(
                isinstance(file, interactions.models.discord.message.Attachment)
                for file in files
            )
        )
    )
    if has_files and is_attachment:
        raise ValueError(
            "Attachments are not files. "
            "Attachments only contain metadata about the file, "
            "not the file itself - to send an attachment, "
            "you need to download it first. Check Attachment.url"
        )
