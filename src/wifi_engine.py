class WiFiQREngine:
    def generate_wifi_string(self, ssid: str, password: str, encryption_type: str, hidden: bool = False) -> str:
        def escape_string(s: str) -> str:
            for char in ["\\", ";", ",", ":"]:
                s = s.replace(char, "\\" + char)
            return s
            
        escaped_ssid = escape_string(ssid)
        escaped_password = escape_string(password)
        
        auth_map = {
            'WPA': 'WPA',
            'WPA2': 'WPA',
            'WPA3': 'WPA',
            'WPA-Enterprise': 'WPA',
            'WPS': 'WPA',
            'WEP': 'WEP',
            'nopass': 'nopass'
        }
        
        t_val = auth_map.get(encryption_type, 'nopass')
        
        hidden_str = "true" if hidden else "false"
        
        if t_val == 'nopass':
            return f"WIFI:S:{escaped_ssid};T:nopass;P:;H:{hidden_str};;"
            
        return f"WIFI:S:{escaped_ssid};T:{t_val};P:{escaped_password};H:{hidden_str};;"
