import os
import csv
import numpy as np

from poi_interlinking import helpers
from poi_interlinking import config


def save_features(fpath, data, delimiter=','):
    h = helpers.StaticValues(config.MLConf.classification_method)
    cols = h.final_cols
    np.savetxt(fpath, data, delimiter=delimiter, header=f'{delimiter}'.join(cols), fmt='%1.3f')


def write_results(fpath, results, delimiter='&'):
    """
    Writes full and averaged experiment results.

    Args:
        fpath (str): Path to write
        results (dict): Contains metrics as keys and the corresponding values \
            values

    Returns:
        None
    """
    file_exists = True
    if not os.path.exists(fpath): file_exists = False

    with open(fpath, 'a+') as file:
        writer = csv.writer(file, delimiter=delimiter)
        if not file_exists:
            writer.writerow(results.keys())
        writer.writerow(results.values())
