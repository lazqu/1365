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
    def test_api_errors_and_invalid_response_fields_save_original_response(self):
        responses = [
            (API_ERROR_RESPONSE, RuntimeError),
            (b"<response><body /></response>", RuntimeError),
            (SUCCESS_RESPONSE.replace(b"<body>", b"<other>").replace(b"</body>", b"</other>"), RuntimeError),
            (SUCCESS_RESPONSE.replace(b"<totalCount>1</totalCount>", b""), RuntimeError),
            (SUCCESS_RESPONSE.replace(b"<items>", b"<other>").replace(b"</items>", b"</other>"), RuntimeError),
            (SUCCESS_RESPONSE.replace(b"<totalCount>1", b"<totalCount>invalid"), ValueError),
            (SUCCESS_RESPONSE.replace(b"<totalCount>1", b"<totalCount>-1"), ValueError),
        ]
        for response, error_type in responses:
            with self.subTest(response=response), tempfile.TemporaryDirectory() as temp_dir:
                with (
                    patch.object(update_data, "__file__", str(Path(temp_dir) / "update_data.py")),
                    patch.object(update_data, "SERVICE_KEY", "test-key"),
                    patch("update_data.urllib.request.urlopen", return_value=io.BytesIO(response)) as urlopen,
                    patch("update_data.time.sleep") as sleep,
                ):
                    with self.assertRaises(error_type):
                        update_data.fetch_page()
                saved = list((Path(temp_dir) / "diagnostics").glob("*.bin"))
                self.assertEqual(len(saved), 1)
                self.assertEqual(saved[0].read_bytes(), response)
                self.assertTrue(saved[0].with_suffix(".json").exists())
                urlopen.assert_called_once()
                sleep.assert_not_called()

    def test_http_error_saves_body_without_request_url(self):
        import json
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(update_data, "__file__", str(Path(temp_dir) / "update_data.py")),
                patch.object(update_data, "SERVICE_KEY", "test-key"),
                patch("update_data.urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                    "https://example.test/?serviceKey=secret", 403, "Forbidden", {}, io.BytesIO(b"denied")
                )),
            ):
                with self.assertRaisesRegex(RuntimeError, "API HTTP Error 403"):
                    update_data.fetch_page()
            saved = next((Path(temp_dir) / "diagnostics").glob("*.bin"))
            self.assertEqual(saved.read_bytes(), b"denied")
            details_text = saved.with_suffix(".json").read_text(encoding="utf-8")
            self.assertEqual(json.loads(details_text)["status"], 403)
            self.assertNotIn("secret", details_text)

    def test_soh_is_replaced_with_spaces_without_changing_other_whitespace(self):
        title = "입소\x01어르신\x01대상\x01공연\x01봉사\t\n"
        response = SUCCESS_RESPONSE.replace(
            b"</progrmRegistNo>",
            ("</progrmRegistNo><progrmSj>" + title + "</progrmSj>").encode("utf-8"),
        )
        with (
            patch.object(update_data, "SERVICE_KEY", "test-key"),
            patch("update_data.urllib.request.urlopen", return_value=io.BytesIO(response)) as urlopen,
            patch("update_data.time.sleep") as sleep,
        ):
            items, count = update_data.fetch_page()
        self.assertEqual(count, 1)
        self.assertEqual(items[0]["progrmSj"], "입소 어르신 대상 공연 봉사\t\n")
        urlopen.assert_called_once()
        sleep.assert_not_called()

    def test_invalid_control_is_preserved_in_diagnostics(self):
        # A remaining syntax error must preserve the unmodified response,
        # including control characters replaced in memory before parsing.
        response = SUCCESS_RESPONSE.replace(b"test-1", "봉사\x00활동 & 오류".encode("utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(update_data, "__file__", str(Path(temp_dir) / "update_data.py")),
                patch.object(update_data, "SERVICE_KEY", "test-key"),
                patch("update_data.urllib.request.urlopen", side_effect=lambda *a, **k: io.BytesIO(response)),
                patch("update_data.time.sleep"),
            ):
                with self.assertRaisesRegex(RuntimeError, "페이지 1 수집 실패"):
                    update_data.fetch_page()
            saved = list((Path(temp_dir) / "diagnostics").glob("*.bin"))
            self.assertEqual(len(saved), 3)
            self.assertTrue(all(path.read_bytes() == response for path in saved))
            import json
            details = json.loads(saved[0].with_suffix(".json").read_text(encoding="utf-8"))
            self.assertIn("\\x00", details["contextRepr"])
            self.assertIn("00", details["contextUtf8Hex"])

    def test_all_xml_forbidden_characters_are_spaces(self):
        forbidden = "".join(chr(n) for n in range(32) if n not in (9, 10, 13)) + "\ufffe\uffff"
        valid = "한글 ★ 😀\t\n\u0020\ud7ff\ue000\ufffd\U00010000\U0010ffff"
        response = SUCCESS_RESPONSE.replace(
            b"</progrmRegistNo>",
            ("</progrmRegistNo><progrmSj>" + forbidden + valid + "</progrmSj>").encode("utf-8"),
        )
        with (
            patch.object(update_data, "SERVICE_KEY", "test-key"),
            patch("update_data.urllib.request.urlopen", return_value=io.BytesIO(response)),
        ):
            items, _ = update_data.fetch_page()
        self.assertEqual(items[0]["progrmSj"], " " * len(forbidden) + valid)
        self.assertEqual(update_data.INVALID_XML_CHARS.sub(" ", "\ud800\udfff"), "  ")
        self.assertEqual(update_data.INVALID_XML_CHARS.sub(" ", "\t\n\r"), "\t\n\r")

    def test_malformed_xml_is_retried_then_succeeds(self):
        with (
            patch.object(update_data, "SERVICE_KEY", "test-key"),
            patch(
                "update_data.urllib.request.urlopen",
                side_effect=[io.BytesIO(b"<response>"), io.BytesIO(SUCCESS_RESPONSE)],
            ) as urlopen,
            patch("update_data.time.sleep") as sleep,
            patch("update_data.save_response_diagnostics") as save,
        ):
            items, count = update_data.fetch_page()
        self.assertEqual(count, 1)
        self.assertEqual(items[0]["progrmRegistNo"], "test-1")
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(1)
        save.assert_called_once()

    def test_persistent_invalid_xml_preserves_existing_data_files(self):
        self.assert_failed_update_preserves_files(
            "페이지 1 수집 실패",
            urlopen_side_effect=lambda *args, **kwargs: io.BytesIO(
                b"<response><item>unescaped & text</item></response>"
            ),
        )

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
