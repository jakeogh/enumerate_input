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

import secrets
import select
import sys
import time
from collections import deque

from icecream import ic


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


def read_by_byte(file_object, byte):    # orig by ikanobori
    buf = b""
    for chunk in iter(lambda: file_object.read(4096), b""):
        buf += chunk
        sep = buf.find(byte)

        while sep != -1:
            ret, buf = buf[:sep], buf[sep + 1:]
            yield ret
            sep = buf.find(byte)
    #ic("fell off end")
    # Decide what you want to do with leftover


def headgen(iterator, count):
    for index, item in enumerate(iterator):
        if (index + 1) > count:
            return
        yield item


def append_to_set(*,
                  iterator,
                  the_set,
                  max_wait_time,
                  min_pool_size,  # the_set always has 1 item
                  verbose=False,
                  debug=False):

    assert max_wait_time > 0.01
    assert min_pool_size >= 2

    time_loops = 0
    eprint("\nWaiting for min_pool_size: {}\n".format(min_pool_size))
    while len(the_set) < min_pool_size:
        start_time = time.time()
        while (time.time() - start_time) < max_wait_time:
            time_loops += 1
            try:
                the_set.add(next(iterator))
            except StopIteration:
                pass

        if time_loops > 1:
            msg = "\nWarning: min_pool_size: {} was not reached in max_wait_time: {}s so actual wait time was: {}x {}s\n"
            msg = msg.format(min_pool_size, max_wait_time, time_loops, max_wait_time * time_loops)
            eprint(msg)

        if len(the_set) < min_pool_size:
            eprint("\nlen(the_set) is {} waiting for min_pool_size: {}\n".format(len(the_set), min_pool_size))

    assert time_loops > 0
    return the_set


# add time-like memory limit
# the longer the max_wait, the larger buffer_set will be,
# resulting in better mixing
def randomize_iterator(iterator,
                       *,
                       min_pool_size,
                       max_wait_time,
                       buffer_set=None,
                       verbose=False,
                       debug=False,):

    assert max_wait_time
    assert min_pool_size

    if min_pool_size < 2:
        min_pool_size = 2

    if not buffer_set:
        buffer_set = set()
        try:
            buffer_set.add(next(iterator))
        except StopIteration:
            pass

    buffer_set = append_to_set(iterator=iterator,
                               the_set=buffer_set,
                               min_pool_size=min_pool_size,
                               max_wait_time=max_wait_time,
                               verbose=verbose,
                               debug=debug)

    while buffer_set:
        try:
            buffer_set.add(next(iterator))
            buffer_set.add(next(iterator))
        except StopIteration:
            pass

        buffer_set_length = len(buffer_set)
        random_index = secrets.randbelow(buffer_set_length)
        next_item = list(buffer_set).pop(random_index)
        buffer_set.remove(next_item)
        if debug:
            eprint("Chose 1 item out of", buffer_set_length)
        if debug:
            eprint("len(buffer_set):", buffer_set_length - 1)
        if verbose:
            ic(len(buffer_set), random_index, next_item)

        yield next_item


def iterate_input(null=False,
                   strings=None,
                   dont_decode=False,
                   head=False,
                   tail=False,
                   random=False,
                   loop=False,
                   verbose=False,
                   debug=False,):

    byte = b'\n'
    if null:
        byte = b'\x00'

    stdin_given = select.select([sys.stdin,], [], [], 0.0)[0]
    if verbose:
        ic(stdin_given)

    if strings and stdin_given:
        raise ValueError("Both arguments AND stdin were proveded.")

    if strings:
        iterator = strings
    else:
        iterator = read_by_byte(sys.stdin.buffer, byte=byte)
        if verbose:
            ic('waiting for input', byte)

    if random:
        iterator = randomize_iterator(iterator,
                                      min_pool_size=1,
                                      max_wait_time=1,)

    if head:
        iterator = headgen(iterator, head)

    if tail:  # this seems like the right order, can access any "tail"
        iterator = deque(iterator, maxlen=tail)

    lines_output = 0
    for index, string in enumerate(iterator):
        if debug:
            ic(index, string)

        if not dont_decode:
            if isinstance(string, bytes):
                string = string.decode('utf8')

        yield string
        lines_output += 1


def enumerate_input(*,
                    iterator,
                    null,
                    verbose=False,
                    debug=False,
                    head=None,
                    tail=None,):

    inner_iterator = iterate_input(strings=iterator,
                                    null=null,
                                    head=head,
                                    tail=tail,
                                    debug=debug,
                                    verbose=verbose,)

    for index, thing in enumerate(inner_iterator):
        yield index, thing
