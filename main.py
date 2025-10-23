import json
from pathlib import Path

from combat import CombatManager
from movement import MovementManager
from potion_manager import PotionManager
from vision import Vision


def load_settings(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def main():
    base = Path(__file__).parent
    settings = load_settings(base / 'config' / 'settings.json')

    vision = Vision(settings)
    combat = CombatManager(settings, vision)
    movement = MovementManager(settings, vision)
    potion = PotionManager(settings, vision)

    print('Boilerplate initialized. Implement bot logic in modules.')


if __name__ == '__main__':
    main()
