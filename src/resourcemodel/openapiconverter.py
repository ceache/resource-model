"""Create openapi spec from resource schema.
"""

import imp
import logging
import os
import re
import sys

import yaml
from . import openapiv3
from . import utils

_LOG = logging.getLogger(__name__)
_EXIT_STATUS = 0


def load_class_from_module(modulefile, major_version):
    """
    Load module file
    """
    openapispec_class = None
    modulebasepath = os.path.dirname(modulefile)
    sys.path.append(modulebasepath)
    inputmodule = os.path.splitext(modulefile)[0]
    modulename = os.path.basename(inputmodule)
    regex = re.compile(r"^openapi(v[0-9]+)$")
    result = regex.match(modulename)
    module_version = result.groups()[0]
    if major_version == module_version:
        modulespec = imp.find_module(modulename)
        module = imp.load_module(modulename, *modulespec)
        classname = "Version" + module_version.upper()
        openapispec_class = getattr(module, classname)
    return openapispec_class


def create_openapi_spec(
    openapi, schemafile, openapidir, outfmt, inputmodule=None
):
    """Create openapi spec for each resource.
    """
    schema = open(schemafile).read()
    try:
        value = yaml.safe_load(schema)
    except yaml.YAMLError as err:
        sys.exit("Yaml Error in {0}: {1}".format(schemafile, err))
    if "rpconly" in value and value["rpconly"]:
        utils.check_rpconlybasic_fields(value, schemafile)
    else:
        utils.check_basic_fields(value, schemafile)
    mimetype = utils.create_mime_type(value)
    version = "_".join(mimetype.split(".")[-3::])
    major_version = mimetype.split(".")[-3]

    # get tag
    openapi["tags"].append(
        {"name": value["name"], "description": value["description"]}
    )
    openapi["info"] = {
        "version": value["version"],
        "title": value["name"],
        "description": "openapi spec for this resource",
    }
    specfile = os.path.join(openapidir, mimetype)
    global _EXIT_STATUS  # pylint: disable=global-statement
    if inputmodule:
        specclass = load_class_from_module(inputmodule, major_version)
        if specclass:
            specobj = specclass(
                openapi,
                specfile,
                value,
                outfmt,
                mimetype,
                version,
                schemafile,
                openapidir,
            )
            specobj.create_spec()
            specobj.write()
            if specobj.error:
                _EXIT_STATUS = 1
        else:
            msg = f"Unable to load {inputmodule}"
            sys.exit(msg)
    else:
        v3specobj = openapiv3.VersionV3(
            openapi,
            specfile,
            value,
            outfmt,
            mimetype,
            version,
            schemafile,
            openapidir,
        )
        v3specobj.create_spec()
        v3specobj.write()
        if v3specobj.error:
            _EXIT_STATUS = 1
