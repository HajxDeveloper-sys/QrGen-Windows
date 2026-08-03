import pytest
from src.utils import validate_url, sanitize_filename, get_timestamp_string


class TestUtils:
    def test_validate_url_valid(self):
        assert validate_url("https://example.com") is True
        assert validate_url("http://google.com/search?q=test") is True

    def test_validate_url_invalid_incomplete(self):
        assert validate_url("https://") is False
        assert validate_url("http://") is False

    def test_validate_url_invalid_scheme(self):
        assert validate_url("ftp://example.com") is False
        assert validate_url("just_text") is False

    def test_sanitize_filename(self):
        assert sanitize_filename("file/name:invalid?.png") == "file_name_invalid_.png"

    def test_get_timestamp_string(self):
        timestamp = get_timestamp_string()
        assert len(timestamp) == 15
        assert "_" in timestamp
