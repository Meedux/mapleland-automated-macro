## Setup

1. Install Python 3.11+.
2. Install dependencies: `pip install -r requirements.txt`
   - Note: easyocr may take some time to download models on first use
3. Place template images in `assets/mob_templates/` and `assets/ui_elements/` (left_char.png, right_char.png, rope.png, reduser.png, ch.png, mainch.png, etc.).
4. Configure settings.json with your preferences (preconditions, auth, hotkeys, routes, buffs, etc.).
5. Run: `python main.py`

## Features

- **Precondition Verification**: Checks OS, resolution, scaling before starting.
- **OCR**: Built-in EasyOCR for HP/MP reading and nickname capture (no external dependencies)
- **Route Configuration**: Define custom hunting routes with boundaries and actions.
- **Advanced Monster Recognition**: Configurable ranges, directions, and recognition rates.
- **Buff Scheduling**: Automatic buff casting with intervals and randomization.
- **Real-time Settings**: Settings changes apply immediately without restart
- **Debug Overlay**: Real-time display of HP/MP, position, current action.
- **In-App Terminal**: View real-time logs and program output within the GUI
- **Simulation Mode**: Run without actual input for testing.
- **OCR**: Built-in EasyOCR for text recognition (no external Tesseract required)
- **Monster detection and combat**
- **Auto-potion (HP/MP)**
- **User detection and channel change**
- **Rope climbing**
- **Modern UI with extensive settings panels**
- **English/Korean language support**

## Configuration

Edit `config/settings.json` to customize:
- **Preconditions**: Configurable OS, resolution, scaling expectations (verification checks against these)
- Auth: Login credentials
- Hotkeys: All key bindings
- Combat: Skill sequences and delays
- Potion: HP/MP thresholds and keys
- Vision: Template paths and OCR settings
- Movement: Speed factors
- Monsters: Template lists and recognition settings
- Routes: Hunting routes with actions
- Buffs: Automatic buff management
- Misc: Various behavior flags
- UI: Language and theme
- Debug: Overlay and simulation options

## Testing

Run tests: `python -m unittest test_bot.py`
