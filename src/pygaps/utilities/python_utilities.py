"""Utilities for different python functionality."""


def _one_pass(iters):
    i = 0
    while i < len(iters):
        try:
            yield next(iters[i])
        except StopIteration:
            del iters[i]
        else:
            i += 1


def zip_varlen(*iterables):
    iters = [iter(it) for it in iterables]
    while True:  # broken when an empty tuple is given by _one_pass
        val = tuple(_one_pass(iters))
        if val:
            yield val
        else:
            break


def grouped(iterable, n):
    return zip_varlen(*[iter(iterable)]*n)
