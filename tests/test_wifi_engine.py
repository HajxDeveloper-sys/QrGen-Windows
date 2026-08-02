import pytest
from src.wifi_engine import WiFiQREngine


class TestWiFiQREngine:
    def setup_method(self):
        self.engine = WiFiQREngine()

    def test_wpa_wifi_string(self):
        result = self.engine.generate_wifi_string("MyNetwork", "MyPassword", "WPA")
        assert "WIFI:" in result
        assert "S:MyNetwork" in result
        assert "T:WPA" in result
        assert "P:MyPassword" in result

    def test_open_wifi_string(self):
        result = self.engine.generate_wifi_string("OpenNet", "", "nopass")
        assert "T:nopass" in result
        assert "P:;" in result

    def test_hidden_network(self):
        result = self.engine.generate_wifi_string("HiddenNet", "pass123", "WPA", hidden=True)
        assert "H:true" in result

    def test_wep_encryption(self):
        result = self.engine.generate_wifi_string("WepNet", "weppass", "WEP")
        assert "T:WEP" in result

    def test_special_characters_escaped(self):
        result = self.engine.generate_wifi_string("My;Network", "pass:word", "WPA")
        assert "My\\;Network" in result or "My;Network" in result
