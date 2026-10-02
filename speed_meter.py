#!/usr/bin/env python3
"""Measure download speed by requesting the same URL sequentially."""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request


DEFAULT_REQUESTS = 10
CHUNK_SIZE = 64 * 1024
VERSION = "1.0.0"


def download_once(url: str, timeout: float) -> tuple[int, float]:
    """Download *url* fully and return (downloaded bytes, elapsed seconds)."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "internet-speed-meter/1.0"},
    )
    started_at = time.perf_counter()
    downloaded = 0

    with urllib.request.urlopen(request, timeout=timeout) as response:
        while chunk := response.read(CHUNK_SIZE):
            downloaded += len(chunk)

    return downloaded, time.perf_counter() - started_at


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="speed-meter",
        description="Последовательно скачивает URL и измеряет среднюю скорость.",
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
        help=f"число запросов (по умолчанию: {DEFAULT_REQUESTS})",
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


def main() -> int:
    args = parse_args()
    total_bytes = 0
    total_seconds = 0.0

    print(f"URL: {args.url}")
    print(f"Запросов: {args.requests}\n")

    for number in range(1, args.requests + 1):
        try:
            downloaded, elapsed = download_once(args.url, args.timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            print(f"[{number:02d}/{args.requests}] Ошибка: {error}", file=sys.stderr)
            return 1

        total_bytes += downloaded
        total_seconds += elapsed
        print(
            f"[{number:02d}/{args.requests}] "
            f"{elapsed:.3f} с, {downloaded / 1_000_000:.3f} MB"
        )

    average_seconds = total_seconds / args.requests
    total_megabytes = total_bytes / 1_000_000
    speed_mbps = total_megabytes / total_seconds if total_seconds else 0.0

    print("\nИтоги:")
    print(f"Среднее время запроса: {average_seconds:.3f} с")
    print(f"Скачано данных:        {total_megabytes:.3f} MB ({total_bytes} байт)")
    print(f"Средняя скорость:      {speed_mbps:.3f} MB/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
