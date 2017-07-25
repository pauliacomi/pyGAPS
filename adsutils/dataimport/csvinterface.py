"""
This module contains the csv interface for returning data such as sample names
"""

import os
import os.path
import pandas as pd

import adsutils

def samples_parser(csv_path):

    samples_df = pd.read_csv(csv_path)
    samples_dict = samples_df.to_dict(orient='index')

    samples = []

    for row in samples_dict:
        sample = adsutils.sample(samples_dict[row])
        samples.append(sample)

    return samples
