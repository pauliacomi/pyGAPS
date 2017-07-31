"""
This module contains the csv interface for returning data such as sample names
"""

import pandas

import adsutils


def samples_parser(csv_path):

    samples_df = pandas.read_csv(csv_path)
    samples_dict = samples_df.to_dict(orient='index')

    samples = []

    for row in samples_dict:
        sample = adsutils.Sample(samples_dict[row])
        samples.append(sample)

    return samples
