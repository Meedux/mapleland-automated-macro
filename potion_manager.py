from typing import Any, Dict


class PotionManager:
    def __init__(self, settings: Dict[str, Any], vision):
        self.settings = settings
        self.vision = vision

    def check_and_use(self):
        pass
