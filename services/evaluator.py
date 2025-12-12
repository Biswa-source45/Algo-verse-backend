from app.utils.output import normalize

def is_correct(expected: str, actual: str) -> bool:
    return normalize(expected) == normalize(actual)
