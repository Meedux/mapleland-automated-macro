import pyautogui
import time
from typing import Any, Dict


class PotionManager:
    def __init__(self, settings: Dict[str, Any], vision):
        self.settings = settings
        self.vision = vision

    def check_and_use(self):
        hp_current, hp_max, mp_current, mp_max = self.vision.read_hp_mp()
        if hp_current and hp_max:
            hp_percentage = (hp_current / hp_max) * 100
            if hp_percentage < 50:
                if not (hp_percentage < 20 and str(hp_max)[0] == '4'):
                    pyautogui.press('del')
        if mp_current and mp_max:
            mp_percentage = (mp_current / mp_max) * 100
            if mp_percentage < 30:
                if not (mp_percentage < 20 and str(mp_max)[0] == '4'):
                    pyautogui.press('end')
