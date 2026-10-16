MAX_LOAD_FACTOR = 0.75


def _hash_string(text):
    """djb2 string hash, deterministic across runs (unlike Python's own str hash)."""
    h = 5381
    for ch in text:
        h = ((h * 33) + ord(ch)) & 0xFFFFFFFF
    return h


def _hash_key(key):
    if isinstance(key, str):
        return _hash_string(key)
    return hash(key)  # ints, tuples and other hashable keys


class HashTable:
    """Hash table using separate chaining. Average O(1) put/get/delete."""

    def __init__(self, capacity=8):
        self._buckets = [[] for _ in range(capacity)]
        self._size = 0

    @property
    def bucket_count(self):
        return len(self._buckets)

    def load_factor(self):
        return self._size / len(self._buckets)

    def _bucket_for(self, key):
        return self._buckets[_hash_key(key) % len(self._buckets)]

    def put(self, key, value):
        bucket = self._bucket_for(key)
        for pair in bucket:
            if pair[0] == key:
                pair[1] = value  # key already present: update in place
                return
        bucket.append([key, value])
        self._size += 1
        if self.load_factor() > MAX_LOAD_FACTOR:
            self._resize()

    def get(self, key, default=None):
        for stored_key, value in self._bucket_for(key):
            if stored_key == key:
                return value
        return default

    def delete(self, key):
        """Remove key. Returns True if it was present, False otherwise."""
        bucket = self._bucket_for(key)
        for i, pair in enumerate(bucket):
            if pair[0] == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def _resize(self):
        old_pairs = list(self.items())
        self._buckets = [[] for _ in range(len(self._buckets) * 2)]
        for key, value in old_pairs:
            self._bucket_for(key).append([key, value])  # size is unchanged

    def items(self):
        for bucket in self._buckets:
            for key, value in bucket:
                yield key, value

    def __len__(self):
        return self._size

    def __contains__(self, key):
        sentinel = object()
        return self.get(key, sentinel) is not sentinel

    def __getitem__(self, key):
        sentinel = object()
        value = self.get(key, sentinel)
        if value is sentinel:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.put(key, value)


def normalize_title(title):
    """Lowercase and collapse whitespace, so ' two   SUM ' matches 'Two Sum'."""
    return " ".join(title.lower().split())


def build_title_index(problems):
    """Map normalized title -> problem dict, for O(1) lookup by title."""
    index = HashTable()
    for problem in problems:
        index.put(normalize_title(problem["title"]), problem)
    return index
