def _key_of(item, key):
    return item if key is None else key(item)


def _merge(left, right, key, reverse):
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        left_key = _key_of(left[i], key)
        right_key = _key_of(right[j], key)
        # Taking from the left on ties keeps equal items in their original order.
        take_left = left_key >= right_key if reverse else left_key <= right_key
        if take_left:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def merge_sort(items, key=None, reverse=False):
    """Return a new list sorted by key. Stable. O(n log n) time, O(n) extra space.

    key may return a tuple to sort by several fields. It must not return None,
    since None can't be compared with numbers.
    """
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key, reverse)
    right = merge_sort(items[mid:], key, reverse)
    return _merge(left, right, key, reverse)
