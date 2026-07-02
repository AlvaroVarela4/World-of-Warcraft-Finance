def copper_to_gsc(copper: int) -> tuple[int, int, int]:
    """Convierte cobre a la tupla (oro, plata, cobre)."""
    gold, rest = divmod(copper, 10_000)
    silver, copper_rest = divmod(rest, 100)
    return gold, silver, copper_rest


def format_price(copper: int) -> str:
    """Formatea un precio en cobre como '1234o 56p 78c'."""
    gold, silver, copper_rest = copper_to_gsc(copper)
    parts = []
    if gold:
        parts.append(f"{gold:,}o")
    if silver or gold:
        parts.append(f"{silver:02d}p")
    parts.append(f"{copper_rest:02d}c")
    return " ".join(parts)


def to_gold(copper: int) -> float:
    """Devuelve el precio en oro con decimales, útil para gráficas."""
    return copper / 10_000