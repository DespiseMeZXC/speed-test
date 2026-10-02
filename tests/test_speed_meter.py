from __future__ import annotations

import io
import unittest
from unittest.mock import patch

import speed_meter


class FakeResponse:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = iter(chunks)

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, _size: int) -> bytes:
        return next(self._chunks, b"")


class SpeedMeterTests(unittest.TestCase):
    def test_download_once_counts_all_received_bytes(self) -> None:
        response = FakeResponse([b"abc", b"12345"])

        with (
            patch("speed_meter.urllib.request.urlopen", return_value=response),
            patch("speed_meter.time.perf_counter", side_effect=[10.0, 12.5]),
        ):
            downloaded, elapsed = speed_meter.download_once(
                "https://example.com/file.bin",
                timeout=5.0,
            )

        self.assertEqual(downloaded, 8)
        self.assertEqual(elapsed, 2.5)

    def test_cli_runs_ten_sequential_requests_and_prints_summary(self) -> None:
        results = [(2_000_000, 0.5)] * 10
        output = io.StringIO()

        with (
            patch("speed_meter.download_once", side_effect=results) as download,
            patch(
                "speed_meter.sys.argv",
                ["speed-meter", "https://example.com/heavy.jpg"],
            ),
            patch("sys.stdout", output),
        ):
            exit_code = speed_meter.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(download.call_count, 10)
        self.assertIn("Среднее время запроса: 0.500 с", output.getvalue())
        self.assertIn("Скачано данных:        20.000 MB", output.getvalue())
        self.assertIn("Средняя скорость:      4.000 MB/s", output.getvalue())


if __name__ == "__main__":
    unittest.main()
