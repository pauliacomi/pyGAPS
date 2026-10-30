"""Utilities for working with pandas dataframes."""

import pandas


def try_numeric(series):
    """Try to convert a pandas series to numeric, otherwise return the original series."""
    try:
        return pandas.to_numeric(series, errors='raise')
    except ValueError:
        return series
