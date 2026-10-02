#!/usr/bin/env python3
"""Measure download speed with concurrent asyncio tasks."""

from __future__ import annotations

import argparse
import asyncio
import sys
import urllib.error

from speed_meter import DEFAULT_REQUESTS, VERSION, download_once


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="speed-meter-async",
        description="Параллельно скачивает URL и измеряет среднюю скорость.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    parser.add_argument("url", help="URL большого файла или изображения")
    parser.add_argument(
        "-n",
        "--requests",
        type=int,
        default=DEFAULT_REQUESTS,
        help=f"число параллельных запросов (по умолчанию: {DEFAULT_REQUESTS})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="тайм-аут одного запроса в секундах (по умолчанию: 60)",
    )
    args = parser.parse_args()

    if args.requests <= 0:
        parser.error("число запросов должно быть больше нуля")
    if args.timeout <= 0:
        parser.error("тайм-аут должен быть больше нуля")
    return args


async def run_downloads(
    url: str,
    requests: int,
    timeout: float,
) -> list[tuple[int, float]]:
    """Run blocking downloads concurrently without blocking the event loop."""
    tasks = [
        asyncio.to_thread(download_once, url, timeout)
        for _ in range(requests)
    ]
    return await asyncio.gather(*tasks)


async def async_main(args: argparse.Namespace | None = None) -> int:
    if args is None:
        args = parse_args()
    print(f"URL: {args.url}")
    print(f"Параллельных запросов: {args.requests}\n")

    started_at = asyncio.get_running_loop().time()
    try:
        results = await run_downloads(args.url, args.requests, args.timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    wall_seconds = asyncio.get_running_loop().time() - started_at

    total_bytes = 0
    total_request_seconds = 0.0
    for number, (downloaded, elapsed) in enumerate(results, start=1):
        total_bytes += downloaded
        total_request_seconds += elapsed
        print(
            f"[{number:02d}/{args.requests}] "
            f"{elapsed:.3f} с, {downloaded / 1_000_000:.3f} MB"
        )

    average_seconds = total_request_seconds / args.requests
    total_megabytes = total_bytes / 1_000_000
    speed_mbps = total_megabytes / wall_seconds if wall_seconds else 0.0

    print("\nИтоги:")
    print(f"Среднее время запроса: {average_seconds:.3f} с")
    print(f"Общее время теста:     {wall_seconds:.3f} с")
    print(f"Скачано данных:        {total_megabytes:.3f} MB ({total_bytes} байт)")
    print(f"Общая скорость:        {speed_mbps:.3f} MB/s")
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
