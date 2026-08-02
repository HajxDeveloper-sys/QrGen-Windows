class VCardEngine:
    def generate_vcard_string(self, first_name: str, last_name: str, phone: str = '', email: str = '', company: str = '', title: str = '', website: str = '', address: str = '') -> str:
        lines = []
        lines.append("BEGIN:VCARD")
        lines.append("VERSION:3.0")
        lines.append(f"N:{last_name};{first_name}")
        lines.append(f"FN:{first_name} {last_name}")
        
        if phone:
            lines.append(f"TEL:{phone}")
        if email:
            lines.append(f"EMAIL:{email}")
        if company:
            lines.append(f"ORG:{company}")
        if title:
            lines.append(f"TITLE:{title}")
        if website:
            lines.append(f"URL:{website}")
        if address:
            lines.append(f"ADR:{address}")
            
        lines.append("END:VCARD")
        
        return "\n".join(lines)
