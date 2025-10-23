from typing import Any, Dict


class CombatManager:
    def __init__(self, settings: Dict[str, Any], vision):
        self.settings = settings
        self.vision = vision

    def find_targets(self):
        return []

    def attack_sequence(self, target):
        pass
