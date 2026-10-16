def _key_of(item, key):
    return item if key is None else key(item)


def lower_bound(items, target, key=None):
    """Index of the first item whose key is >= target (len(items) if none).

    items must be sorted by key. Runs in O(log n).
    """
    lo, hi = 0, len(items)
    while lo < hi:
        mid = (lo + hi) // 2
        if _key_of(items[mid], key) < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(items, target, key=None):
    """Index of the first item whose key is > target (len(items) if none)."""
    lo, hi = 0, len(items)
    while lo < hi:
        mid = (lo + hi) // 2
        if _key_of(items[mid], key) <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def binary_search(items, target, key=None):
    """Index of an item whose key equals target, or -1 if there is none."""
    i = lower_bound(items, target, key)
    if i < len(items) and _key_of(items[i], key) == target:
        return i
    return -1


def find_in_range(items, low, high, key=None):
    """All items with low <= key <= high, from a list sorted by key."""
    start = lower_bound(items, low, key)
    end = upper_bound(items, high, key)
    return items[start:end]
