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


import sys
from math import inf
from typing import Optional

import click
from clicktool import click_add_options
from clicktool import click_global_options
from icecream import ic

from enumerate_input import _enumerate_input


@click.command()
@click.argument("args", type=str, nargs=-1)
@click.option('--count', type=float, default=inf)
@click_add_options(click_global_options)
@click.pass_context
def cli(ctx,
        args: Optional[tuple[str]],
        verbose: Union[bool, int, float],
        verbose_inf: bool,
        count: bool,
        ):

    if verbose:
        ic(sys.stdout.isatty())

    for index, arg in _enumerate_input(iterator=args,
                                       verbose=verbose,
                                       ):
        if verbose:
            ic(index, arg)
        if count:
            if count > (index + 1):
                ic(count)
                sys.exit(0)

        ic(arg)
