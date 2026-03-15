from __future__ import annotations

import json
import random
import re
import string
from typing import Any


def split_payloads(raw_message: str) -> list[str]:
    matches = re.split(r"~m~\d+~m~", raw_message)
    return [match for match in matches if match]


def encode_message(function: str, parameters: list[Any]) -> str:
    payload = json.dumps({"m": function, "p": parameters}, separators=(",", ":"))
    return f"~m~{len(payload)}~m~{payload}"


def encode_raw(payload: str) -> str:
    return f"~m~{len(payload)}~m~{payload}"


def generate_session(prefix: str) -> str:
    suffix = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
    return f"{prefix}_{suffix}"


def cookie_header_value(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in sorted(cookies.items()))
