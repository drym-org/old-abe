def call_sequence(seq):
    """
    A test helper to return from a provided sequence of values each time
    the function is called.
    """
    ret = {}
    for i, e in enumerate(seq):
        ret[i] = e
    count = 0

    def mock_fn(*args, **kwargs):
        nonlocal count
        val = ret[count]
        count += 1
        return val

    return mock_fn
