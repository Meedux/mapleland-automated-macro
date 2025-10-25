## Setup

1. Install Python 3.11+.
2. Install dependencies: `pip install -r requirements.txt`
   - Note: easyocr may take some time to download models on first use.
3. Place template images in `assets/mob_templates/` and `assets/ui_elements/` (examples: left_char.png, right_char.png, rope.png, reduser.png, ch.png, mainch.png).
4. Configure `config/settings.json` with your preferences (preconditions, auth, hotkeys, routes, buffs, etc.). A default `settings.json` is generated on first run.
5. Run the program:

```powershell
python main.py
```

## Highlights & New UI Flow

- Start now prompts a modern window selector so you explicitly choose which game window the bot should use.
- The selector shows a searchable list of top-level windows, a non-focusing preview, and a Confirm action that:
  - focuses the selected window,
  - validates the focused window contains the game UI (vision sanity-check), and
  - persists your selection in `config/settings.json`.
- A Refresh button in the selector re-enumerates windows while the dialog is open.
- This change prevents unwanted focus-stealing and makes the Start → Select → Confirm → Run flow explicit and robust.

## Features

- Precondition Verification: checks OS, resolution and scaling before allowing start.
- Window Selector: searchable modal to pick and validate the game window (Confirm focuses + verifies via vision).
- Vision & OCR: EasyOCR-based HP/MP reading and nickname capture for robust detection.
- Anti-auto-play detectors: lie detector, other-user detection, chat/enemy detection and alarms.
- Alarms & Notifications: modal alarm with sound that remains until dismissed (Dismiss stops alarm loop).
- Route Configuration: flexible JSON routes with randomization to diversify movement.
- Top-floor handling: detection and escape behaviors to avoid getting stuck.
- Combat & Monster Recognition: configurable templates, recognition ranges and delays.
- Buff scheduling and auto-potions (HP/MP) with thresholds and hotkeys.
- In-app Terminal: logs appear in the GUI when the bot starts.
- Localization: English and Korean UI support (set `ui.language` in settings).
- Simulation Mode: run without sending input for safe testing.

## Configuration

Edit `config/settings.json` to customize:

- Preconditions: OS, resolution, scaling, and other startup checks.
- Auth: login credentials (if used by your workflow).
- Hotkeys: key bindings for start/stop, potions, attack, jump, etc.
- Vision: template paths, OCR thresholds and nick detection settings.
- Movement & Routes: speed factors, route JSON and randomization settings.
- Monsters: recognition templates and behavioral flags.
- Misc: various behavior toggles (user detection, stationary handling, etc.).
- UI: language (en/ko) and theme (light/dark/system).
- Debug: enable debug mode, simulation mode, or overlay options.

The UI provides an in-app settings panel (Settings) that writes changes live to `config/settings.json`.

## Running & Troubleshooting

- If the window selector cannot bring the game to the foreground due to OS focus policies, use the Refresh button or manually focus the game and retry Confirm.
- If vision cannot detect the game UI after focusing, verify your game resolution, scaling, and that the game's window is not minimized or covered by overlays.

## Packaging

You can package this application with PyInstaller or similar tools. Make sure to include the `assets/` folder and any OCR model files required by EasyOCR.

## Testing

Run tests:

```powershell
python -m unittest test_bot.py
```

## Contributing

Contributions welcome — open an issue or PR to discuss changes, UI improvements, or additional detectors.

---
Updated: Added window selector workflow, focused validation, alarms, localization and UI improvements.
