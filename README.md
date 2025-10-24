## Setup

1. Install Python 3.11+.
2. Install dependencies: `pip install -r requirements.txt`
3. Install Tesseract OCR: Download from https://github.com/UB-Mannheim/tesseract/wiki and update path in settings.json if needed.
4. Place template images in `assets/mob_templates/` and `assets/ui_elements/` (left_char.png, right_char.png, rope.png, reduser.png, ch.png, mainch.png, etc.).
5. Run: `python main.py`

## Features

- Character recognition and movement
- Monster detection and combat
- Auto-potion (HP/MP)
- User detection and channel change
- Rope climbing
- Modern UI with English/Korean support
