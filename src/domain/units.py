from typing import Final

_ALIASES: Final[dict[str, str]] = {
    "g": "g",
    "gr": "g",
    "gramme": "g",
    "grammes": "g",
    "kg": "kg",
    "kilo": "kg",
    "ml": "ml",
    "cl": "cl",
    "l": "l",
    "litre": "l",
    "litres": "l",
    "piece": "piece",
    "pieces": "piece",
    "pièce": "piece",
    "pièces": "piece",
    "pc": "piece",
    "pcs": "piece",
    "unite": "piece",
    "unité": "piece",
    "unités": "piece",
}

_BASE_FACTORS: Final[dict[str, tuple[str, float]]] = {
    "g": ("g", 1.0),
    "kg": ("g", 1000.0),
    "ml": ("ml", 1.0),
    "cl": ("ml", 10.0),
    "l": ("ml", 1000.0),
}


def normalize_unit(unit: str | None) -> str | None:
    if unit is None or not unit.strip():
        return None
    cleaned = unit.strip().lower().rstrip(".")
    return _ALIASES.get(cleaned, cleaned)


def convert(quantity: float, from_unit: str | None, to_unit: str | None) -> float | None:
    source = normalize_unit(from_unit)
    target = normalize_unit(to_unit)
    if source == target:
        return quantity
    if source is None or target is None:
        return None
    source_base = _BASE_FACTORS.get(source)
    target_base = _BASE_FACTORS.get(target)
    if source_base is None or target_base is None or source_base[0] != target_base[0]:
        return None
    return quantity * source_base[1] / target_base[1]
