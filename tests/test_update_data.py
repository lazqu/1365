import io
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import update_data


SUCCESS_RESPONSE = b"""\
<response>
  <header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
  <body>
    <totalCount>1</totalCount>
    <items><item><progrmRegistNo>test-1</progrmRegistNo></item></items>
  </body>
</response>
"""

EMPTY_RESPONSE = b"""\
<response>
  <header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
  <body><totalCount>0</totalCount><items /></body>
</response>
"""

API_ERROR_RESPONSE = b"""\
<response>
  <header><resultCode>30</resultCode><resultMsg>Service key error</resultMsg></header>
  <body><totalCount>0</totalCount><items /></body>
</response>
"""


class UpdateDataTests(unittest.TestCase):
    def test_fetch_page_retries_network_error_then_succeeds(self):
        with (
            patch.object(update_data, "SERVICE_KEY", "test-key"),
            patch(
                "update_data.urllib.request.urlopen",
                side_effect=[urllib.error.URLError("timed out"), io.BytesIO(SUCCESS_RESPONSE)],
            ) as urlopen,
            patch("update_data.time.sleep") as sleep,
        ):
            items, total_count = update_data.fetch_page(page_size=1)

        self.assertEqual(total_count, 1)
        self.assertEqual(items[0]["progrmRegistNo"], "test-1")
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_successful_empty_response_is_not_a_fetch_error(self):
        with (
            patch.object(update_data, "SERVICE_KEY", "test-key"),
            patch(
                "update_data.urllib.request.urlopen",
                return_value=io.BytesIO(EMPTY_RESPONSE),
            ),
        ):
            items, total_count = update_data.fetch_page()

        self.assertEqual(items, [])
        self.assertEqual(total_count, 0)

    def test_timeout_exhaustion_preserves_existing_data_files(self):
        self.assert_failed_update_preserves_files(
            "페이지 1 수집 실패",
            urlopen_side_effect=urllib.error.URLError("timed out"),
        )

    def test_api_error_preserves_existing_data_files(self):
        self.assert_failed_update_preserves_files(
            "API Error 30",
            urlopen_return_value=io.BytesIO(API_ERROR_RESPONSE),
        )

    def assert_failed_update_preserves_files(
        self, error_message, urlopen_side_effect=None, urlopen_return_value=None
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_path = temp_path / "data.json"
            js_path = temp_path / "data.js"
            json_path.write_text("existing json", encoding="utf-8")
            js_path.write_text("existing js", encoding="utf-8")

            with (
                patch.object(update_data, "__file__", str(temp_path / "update_data.py")),
                patch.object(update_data, "SERVICE_KEY", "test-key"),
                patch(
                    "update_data.urllib.request.urlopen",
                    side_effect=urlopen_side_effect,
                    return_value=urlopen_return_value,
                ),
                patch("update_data.time.sleep"),
            ):
                with self.assertRaisesRegex(RuntimeError, error_message):
                    update_data.run_update()

            self.assertEqual(json_path.read_text(encoding="utf-8"), "existing json")
            self.assertEqual(js_path.read_text(encoding="utf-8"), "existing js")


if __name__ == "__main__":
    unittest.main()