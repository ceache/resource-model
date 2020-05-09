"""Script to create openapi spec from resource schema
"""

import argparse
import copy
import errno
import logging
import os

from . import openapiconverter
from . import utils

_LOG = logging.getLogger(__name__)


def _run_cli_parser():
    """Setup the CLI parser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outfmt", required=False, default="json", help="yaml or json"
    )
    parser.add_argument("--indir", required=False, help="input directory")
    parser.add_argument("--outdir", required=True, help="output directory")
    parser.add_argument(
        "--infile", required=False, help="full path to a schema file"
    )
    parser.add_argument(
        "-m", "--module", required=False, help="Module used for creating spec"
    )
    args = parser.parse_args()
    if args.infile and not args.indir:
        args.indir = os.path.dirname(args.infile)
    # Ensure outdir exists and/or can be created.
    try:
        os.makedirs(args.outdir)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise
    assert os.access(args.outdir, os.W_OK)
    return args


def convert_to_openapispec():
    """convert a resource schema to openapi 3 specifications.
    """
    log_format = "[%(filename)s:%(lineno)d][%(levelname)s]: %(message)s"
    logging.basicConfig(format=log_format, level=logging.INFO)
    args = _run_cli_parser()

    openapiglobal = dict()
    openapiglobal["openapi"] = "3.0.0"  # Move this to spec generator.
    openapiglobal["tags"] = list()
    openapiglobal["paths"] = dict()
    openapiglobal["components"] = dict()
    openapiglobal["components"]["schemas"] = dict()
    info = dict()
    openapiglobal["info"] = info

    openapidir = args.outdir
    utils.dump_file_to_openapidir(args.indir, openapidir)

    resources_list = (
        [args.infile]
        if args.infile
        else [
            schema
            for schema in os.listdir(args.indir)
            if os.path.isfile(schema)
        ]
    )

    for resource_file in resources_list:
        openapi = dict()
        openapi = copy.deepcopy(openapiglobal)

        openapiconverter.create_openapi_spec(
            openapi, resource_file, openapidir, args.outfmt, args.module,
        )


__all__ = ("convert_to_openapispec",)
