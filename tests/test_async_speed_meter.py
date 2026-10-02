from __future__ import annotations

import asyncio
import io
import unittest
from unittest.mock import patch

import async_speed_meter


class AsyncSpeedMeterTests(unittest.TestCase):
    def test_run_downloads_starts_requested_number_of_jobs(self) -> None:
        async def fake_to_thread(function, *args):
            return function(*args)

        with (
            patch("async_speed_meter.asyncio.to_thread", side_effect=fake_to_thread) as to_thread,
            patch("async_speed_meter.download_once", return_value=(1_000_000, 0.25)),
        ):
            results = asyncio.run(
                async_speed_meter.run_downloads(
                    "https://example.com/file.bin",
                    requests=10,
                    timeout=5.0,
                )
            )

        self.assertEqual(len(results), 10)
        self.assertEqual(to_thread.call_count, 10)

    def test_async_cli_prints_parallel_summary(self) -> None:
        results = [(2_000_000, 0.5)] * 10
        output = io.StringIO()

        async def fake_run_downloads(*_args):
            return results

        with (
            patch(
                "async_speed_meter.run_downloads",
                new=fake_run_downloads,
            ),
            patch(
                "async_speed_meter.sys.argv",
                ["speed-meter-async", "https://example.com/heavy.jpg"],
            ),
            patch("sys.stdout", output),
        ):
            exit_code = asyncio.run(async_speed_meter.async_main())

        self.assertEqual(exit_code, 0)
        self.assertIn("Параллельных запросов: 10", output.getvalue())
        self.assertIn("Скачано данных:        20.000 MB", output.getvalue())
        self.assertIn("Общая скорость:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
