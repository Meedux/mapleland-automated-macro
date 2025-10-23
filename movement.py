from typing import Any, Dict


class MovementManager:
    def __init__(self, settings: Dict[str, Any], vision):
        self.settings = settings
        self.vision = vision

    def patrol(self):
        pass

    def navigate_to(self, x: int, y: int):
        pass
