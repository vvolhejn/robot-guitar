import functools
import logging
import time
from datetime import datetime
from typing import Annotated

import ntplib
from pydantic import PlainValidator  # pyright: ignore[reportMissingTypeStubs]

logger = logging.getLogger(__name__)


# Only do this once per run to get a consistent timer
@functools.cache
def get_ntp_offset_sec() -> float:
    c = ntplib.NTPClient()

    # Get a bit more precision by averaging multiple requests
    n_requests = 1  # more can lead to getting blocked by the NTP server
    offsets = []
    for _ in range(n_requests):
        offsets.append(c.request("pool.ntp.org").offset)
    offset = sum(offsets) / len(offsets)

    logger.info(f"Average NTP offset: {offset}")

    return offset


def get_network_timestamp() -> float:
    ntp_offset = get_ntp_offset_sec()
    client_time = time.time()
    network_time = client_time + ntp_offset
    return network_time


def get_network_datetime() -> datetime:
    return datetime.fromtimestamp(get_network_timestamp())


def unix_to_datetime(v: float | str | datetime) -> datetime:
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        return datetime.fromisoformat(v)
    if isinstance(v, float):
        return datetime.fromtimestamp(v)
    raise ValueError(f"Invalid value: {v!r}")


UnixTimestamp = Annotated[datetime, PlainValidator(unix_to_datetime)]
