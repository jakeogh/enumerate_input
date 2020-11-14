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


#import os
import sys
import click
from icecream import ic
from enumerate_input import enumerate_input

# import IPython; IPython.embed()
# import pdb; pdb.set_trace()
# from pudb import set_trace; set_trace(paused=False)

# DONT CHANGE FUNC NAME
@click.command()
@click.argument("args", type=str, nargs=-1)
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option('--simulate', is_flag=True)
@click.option('--count', type=str)
@click.option("--printn", is_flag=True)
def cli(args,
        verbose,
        debug,
        simulate,
        count,
        printn,):

    null = not printn

    if verbose:
        ic(sys.stdout.isatty())

    if not args:
        ic('waiting for input')

    for index, arg in enumerate_input(iterator=args,
                                      null=null,
                                      debug=debug,
                                      verbose=verbose):
        if verbose or simulate:
            ic(index, arg)
        if count:
            if count > (index + 1):
                ic(count)
                sys.exit(0)

        if simulate:
            continue

        ic(arg)
