from pathlib import Path

path = Path(__file__).parent


def get(name):
    return path / name
