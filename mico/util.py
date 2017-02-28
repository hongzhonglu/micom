"""Holds utility functions for other modules."""

import cobra.io as io
import os.path as path
import pickle
from six.moves.urllib.parse import urlparse
import six.moves.urllib.request as urlreq
import tempfile
import pandas as pd
from mico.logger import logger


_read_funcs = {".xml": io.read_sbml_model,
               ".gz": io.read_sbml_model,
               ".mat": io.load_matlab_model,
               ".json": io.load_json_model,
               ".pickle": lambda fn: pickle.load(open(fn, "rb"))}


def download_model(url, folder="."):
    """Download a model."""
    dest = path.join(folder, path.basename(url))
    urlreq.urlretrieve(url, dest)

    return dest


def _read_model(file):
    """Read a model from a local file."""
    _, ext = path.splitext(file)
    read_func = _read_funcs[ext]
    return read_func(file)


def load_model(filepath):
    """Load a cobra model from several file types."""
    logger.info("reading model from {}".format(filepath))
    with tempfile.TemporaryDirectory() as tmpdir:
        parsed = urlparse(filepath)
        if parsed.scheme and parsed.netloc:
            filepath = download_model(filepath, folder=tmpdir)
        return _read_model(filepath)


def serialize_models(files, dir="."):
    """Convert several models to Python pickles."""
    for f in files:
        fname, _ = path.splitext(path.basename(f))
        model = load_model(f)
        logger.info("serializing {}".format(f))
        pickle.dump(model, open(path.join(dir, fname + ".pickle"), "wb"))


def fluxes_from_primals(model, info):
    """Extract a list of fluxes from the model primals."""
    suffix = "__" + info.id.strip()
    primals = model.solver.primal_values
    rxns = model.reactions.query(lambda r: info.id == r.community_id)
    rids = [r.id.replace(suffix, "") for r in rxns]

    fluxes = (primals[rxn.forward_variable.name] -
              primals[rxn.reverse_variable.name] for rxn in rxns)
    fluxes = pd.Series(fluxes, rids, name=info.id)

    return fluxes