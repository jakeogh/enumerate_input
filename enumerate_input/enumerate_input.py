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

import os
import secrets
#import select
import sys
import time
from collections import deque
from stat import S_ISFIFO


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint


def read_by_byte(file_object,
                 byte,
                 verbose: bool,
                 debug: bool,):    # orig by ikanobori
    if verbose:
        ic(byte)
    buf = b""
    for chunk in iter(lambda: file_object.read(4096), b""):
        buf += chunk
        sep = buf.find(byte)
        if debug:
            ic(buf, sep)

        while sep != -1:
            ret, buf = buf[:sep], buf[sep + 1:]
            yield ret
            sep = buf.find(byte)
    if debug:
        ic('fell off end:', ret, buf)
    # Decide what you want to do with leftover


def skipgen(*,
            iterator,
            count,
            verbose: bool,
            debug: bool,):
    if verbose:
        ic(count)
    if debug:
        ic(iterator)
    for index, item in enumerate(iterator):
        if debug:
            ic(index, item)
        if (index + 1) <= count:
            continue
        yield item


def headgen(*,
            iterator,
            count,
            verbose: bool,
            debug: bool,):
    if verbose:
        ic(count)
    if debug:
        ic(iterator)
    for index, item in enumerate(iterator):
        if debug:
            ic(index, item)
        if (index + 1) > count:
            return
        yield item


def append_to_set(*,
                  iterator,
                  the_set,
                  max_wait_time,
                  min_pool_size,  # the_set always has 1 item
                  verbose: bool,
                  debug: bool,):

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
            msg = msg.format(min_pool_size,
                             max_wait_time,
                             time_loops,
                             max_wait_time * time_loops,)
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


def iterate_input(iterator,
                  null: bool,
                  disable_stdin: bool,
                  dont_decode: bool,
                  head: bool,
                  tail: bool,
                  skip: bool,
                  random: bool,
                  loop: bool,
                  verbose: bool,
                  debug: bool,):

    byte = b'\n'
    if null:
        byte = b'\x00'

    if skip in [0, True, None] or (skip <= 0):
        raise ValueError('skip must be False or a positive integer, not:', skip)
    if head in [0, True, None] or (head <= 0):
        raise ValueError('head must be False or a positive integer, not:', head)
    if tail in [0, True, None] or (tail <= 0):
        raise ValueError('tail must be False or a positive integer, not:', tail)

    assert skip is not None
    assert head is not None
    assert tail is not None

    if not iterator:
        if disable_stdin:
            raise ValueError('iterator is None and disable_stdin=True, nothing to read')

    if disable_stdin:
        stdin_is_a_fifo = False
    else:
        stdin_is_a_fifo = S_ISFIFO(os.fstat(sys.stdin.fileno()).st_mode)
        stdin_is_a_tty = sys.stdin.isatty()
        #stdin_given = select.select([sys.stdin,], [], [], 0.0)[0]

    if verbose:
        ic(byte, skip, head, tail, null, disable_stdin, random, dont_decode, stdin_is_a_tty, stdin_is_a_fifo)

    if stdin_is_a_fifo:
        iterator = sys.stdin.buffer
        if verbose:
            ic('waiting for input on sys.stdin.buffer', byte)

    if hasattr(iterator, 'read'):
        iterator = read_by_byte(iterator,
                                byte=byte,
                                verbose=verbose,
                                debug=debug,)

    if random:
        if verbose:
            ic(random)
        iterator = randomize_iterator(iterator,
                                      min_pool_size=1,
                                      max_wait_time=1,
                                      verbose=verbose,)
        if debug:
            ic(iterator)

    if skip:
        if verbose:
            ic(skip)
        iterator = skipgen(iterator=iterator,
                           count=skip,
                           verbose=verbose,
                           debug=debug,)
        if debug:
            ic(iterator)

    if head:
        if verbose:
            ic(head)
        iterator = headgen(iterator=iterator,
                           count=head,
                           verbose=verbose,
                           debug=debug,)
        if debug:
            ic(iterator)

    if tail:  # this seems like the right order, can access any "tail"
        if verbose:
            ic(tail)
        iterator = deque(iterator,
                         maxlen=tail,)
        if debug:
            ic(iterator)

    lines_output = 0
    for index, string in enumerate(iterator):
        if debug:
            ic(index, string)

        if not dont_decode:
            if isinstance(string, bytes):
                string = string.decode('utf8')

        if debug:
            ic(len(string))

        yield string
        lines_output += 1


def enumerate_input(*,
                    iterator,
                    skip,
                    head,
                    tail,
                    verbose: bool,
                    debug: bool,
                    null: bool = False,
                    loop: bool = False,
                    disable_stdin: bool = False,
                    random: bool = False,
                    dont_decode: bool = False,
                    progress: bool = False,):

    if progress and (verbose or debug):
        raise ValueError('--progress and --verbose/--debug are mutually exclusive')

    inner_iterator = iterate_input(iterator=iterator,
                                   null=null,
                                   disable_stdin=disable_stdin,
                                   head=head,
                                   tail=tail,
                                   skip=skip,
                                   dont_decode=dont_decode,
                                   loop=loop,
                                   random=random,
                                   debug=debug,
                                   verbose=verbose,)
    if debug:
        ic(inner_iterator)

    for index, thing in enumerate(inner_iterator):
        if progress:
            print(index + 1, file=sys.stderr, end='\r')
        yield index, thing
    if progress:
        print("", file=sys.stderr)
