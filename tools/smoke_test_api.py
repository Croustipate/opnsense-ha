"""Manual smoke test for api.py against a real OPNsense instance.

Usage:
    OPNSENSE_HOST=https://opnsense.bambinette.com:8443 \
    OPNSENSE_KEY=... \
    OPNSENSE_SECRET=... \
    python3 tools/smoke_test_api.py
"""
from __future__ import annotations

import asyncio
import os
import sys

import aiohttp

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "custom_components", "opnsense"
    ),
)

from api import OpnsenseClient  # noqa: E402


async def main() -> None:
    host = os.environ["OPNSENSE_HOST"]
    key = os.environ["OPNSENSE_KEY"]
    secret = os.environ["OPNSENSE_SECRET"]
    async with aiohttp.ClientSession() as session:
        client = OpnsenseClient(session, host, key, secret)
        status = await client.async_get_status()
        print("FirmwareStatus:", status)


if __name__ == "__main__":
    asyncio.run(main())
