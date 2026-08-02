import sys
from pathlib import Path

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def main():
    base_path = get_base_path()
    sys.path.insert(0, str(base_path))
    
    from src.app import QRCodeGeneratorApp
    app = QRCodeGeneratorApp(base_path=base_path)
    app.mainloop()

if __name__ == "__main__":
    main()
