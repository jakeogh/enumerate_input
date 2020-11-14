#!/usr/bin/env python3

# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=W0511  # todo is encouraged
# pylint: disable=C0301  # line too long
# pylint: disable=R0902  # too many instance attributes
# pylint: disable=C0302  # too many lines in module
# pylint: disable=C0103  # single letter var names, func name too descriptive
# pylint: disable=R0911  # too many return statements
# pylint: disable=R0912  # too many branches
# pylint: disable=R0915  # too many statements
# pylint: disable=R0913  # too many arguments
# pylint: disable=R1702  # too many nested blocks
# pylint: disable=R0914  # too many local variables
# pylint: disable=R0903  # too few public methods
# pylint: disable=E1101  # no member for base
# pylint: disable=W0201  # attribute defined outside __init__
# pylint: disable=R0916  # Too many boolean expressions in if statement
## pylint: disable=W0703  # catching too general exception


# TODO:
#   https://github.com/kvesteri/validators
import os
import sys
import click
from pathlib import Path
from icecream import ic
from kcl.iterops import enumerate_input

ic.configureOutput(includeContext=True)
# import IPython; IPython.embed()
# import pdb; pdb.set_trace()
# from pudb import set_trace; set_trace(paused=False)

global APP_NAME
APP_NAME = 'enumerate_input'


# DONT CHANGE FUNC NAME
@click.command()
@click.argument("paths", type=str, nargs=-1)
@click.argument("sysskel",
                type=click.Path(exists=False,
                                dir_okay=True,
                                file_okay=False,
                                path_type=str,
                                allow_dash=False),
                nargs=1,
                required=True)
@click.option('--add', is_flag=True)
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
#@click.option('--ipython', is_flag=True)
@click.option('--simulate', is_flag=True)
@click.option('--count', type=str)
@click.option("--null", is_flag=True)
#@click.group()
def cli(paths,
        sysskel,
        verbose,
        debug,
        ipython,
        simulate,
        count,
        null,):

    if verbose:
        ic(sys.stdout.isatty())

    if not paths:
        ic('waiting for input')

    for index, path in enumerate_input(iterator=paths,
                                       null=null,
                                       debug=debug,
                                       verbose=verbose):
        path = Path(path)

        if verbose or simulate:
            ic(index, path)
        if count:
            if count > (index + 1):
                ic(count)
                sys.exit(0)

        if simulate:
            continue

        with open(path, 'rb') as fh:
            path_bytes_data = fh.read()

#        if ipython:
#            import IPython; IPython.embed()


