"""Monitor topology for pets wandering between screens (pure geometry, no Qt types)."""


def neighbour(rects, current, direction, min_overlap=48):
    """Index of the screen directly left (-1) or right (+1) of rects[current], or None.

    rects: [(x, y, w, h)] in global desktop coordinates. Screens count as neighbours when their
    edges touch (within 8 px) and they overlap vertically by at least `min_overlap` px.
    """
    x, y, w, h = rects[current]
    best = None
    for i, (ox, oy, ow, oh) in enumerate(rects):
        if i == current:
            continue
        touching = abs(ox - (x + w)) <= 8 if direction > 0 else abs((ox + ow) - x) <= 8
        overlap = min(y + h, oy + oh) - max(y, oy)
        if touching and overlap >= min_overlap and (best is None or overlap > best[0]):
            best = (overlap, i)
    return best[1] if best else None


def exits(rects, current):
    """Directions (-1, 1) in which a neighbouring screen exists."""
    return tuple(d for d in (-1, 1) if neighbour(rects, current, d) is not None)
