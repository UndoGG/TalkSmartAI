import os
import re
import random
import string
import uuid
import io
import aiohttp
import aiofiles
import asyncio


def format_seconds(seconds, translator):
    if seconds < 0:
        return translator.t('incorrect_time')

    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    time_parts = []
    if hours > 0:
        time_parts.append(f"{hours} {translator.t('hours')}")
    if minutes > 0:
        time_parts.append(f"{minutes} {translator.t('minutes')}")
    if seconds > 0:
        time_parts.append(f"{seconds} {translator.t('seconds')}")

    if not time_parts:
        return f"0 {translator.t('seconds')}"

    return " ".join(time_parts)


def optimize_spaces(text: str) -> str:
    return re.sub(r'\s+', ' ', text)


def unpack_list(items: list, do_space: bool = True, do_comma: bool = False):
    out = ''
    for item in items:
        if do_comma and item != items[-1]:
            item += ', '
        elif do_space and item != items[-1]:
            item += ' '
        out += item

    return out
