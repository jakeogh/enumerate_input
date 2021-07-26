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
from typing import Optional
from typing import Union

from asserttool import eprint
from asserttool import ic
from asserttool import increment_debug


@increment_debug
def read_by_byte(file_object,
                 byte,
                 verbose: Union[bool, int],
                 debug: Union[bool, int],
                 ) -> bytes:    # orig by ikanobori
    if verbose:
        ic(byte)
    buf = b""
    #for chunk in iter(lambda: file_object.read(131072), b""):
    #for chunk in iter(lambda: file_object.read(8192), b""):
    for chunk in iter(lambda: file_object.read(1024), b""):
        if verbose > 2:
            ic(chunk)
        buf += chunk
        sep = buf.find(byte)
        if verbose > 2:
            ic(buf, sep)

        while sep != -1:
            ret, buf = buf[:sep], buf[sep + 1:]
            yield ret
            sep = buf.find(byte)
    if verbose > 2:
        ic('fell off end:', ret, buf)
    # Decide what you want to do with leftover


@increment_debug
def filtergen(*,
              iterator,
              filter_function: object,
              verbose: bool,
              debug: bool,
              ):
    if verbose:
        ic(filter_function)
    if debug:
        ic(iterator)
    for item in iterator:
        if debug:
            ic(item)
        if not filter_function(item):
            continue
        yield item


@increment_debug
def skipgen(*,
            iterator,
            count,
            verbose: bool,
            debug: bool,
            ):
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


@increment_debug
def headgen(*,
            iterator,
            count,
            verbose: bool,
            debug: bool,
            ):
    if verbose:
        ic(count)
    if debug:
        ic(iterator)
    for index, item in enumerate(iterator):
        if debug:
            ic(index, item)
        yield item
        if debug:
            ic(index + 1, count)
        if (index + 1) == count:
            return


@increment_debug
def append_to_set(*,
                  iterator,
                  the_set: set,
                  max_wait_time: float,
                  min_pool_size: int,  # the_set always has 1 item
                  verbose: bool,
                  debug: bool,
                  ):

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
@increment_debug
def randomize_iterator(iterator,
                       *,
                       min_pool_size: int,
                       max_wait_time: float,
                       buffer_set=None,
                       verbose: bool = False,
                       debug: bool = False,
                       ):

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


@increment_debug
def iterate_input(iterator,
                  null: bool,
                  disable_stdin: bool,
                  dont_decode: bool,
                  head: Optional[int],
                  tail: Optional[int],
                  skip: Optional[int],
                  random: bool,
                  loop: bool,
                  verbose: bool,
                  debug: bool,
                  input_filter_function: object,
                  ):

    byte = b'\n'
    if null:
        byte = b'\x00'

    if skip:
        if isinstance(skip, bool) or (skip <= 0):
            #ic('BUG', skip)
            skip = None
            #raise ValueError('skip must be False or a positive integer, not:', skip)
    if head:
        if isinstance(head, bool) or (head <= 0):
            #ic('BUG', head)
            head = None
            #raise ValueError('head must be False or a positive integer, not:', head)
    if tail:
        if isinstance(tail, bool) or (tail <= 0):
            #ic('BUG', tail)
            tail = None
            #raise ValueError('tail must be False or a positive integer, not:', tail)

    if not iterator:
        if disable_stdin:
            raise ValueError('iterator is None and disable_stdin=True, nothing to read')

    stdin_is_a_tty = sys.stdin.isatty()
    if disable_stdin:
        stdin_is_a_fifo = False
    else:
        stdin_is_a_fifo = S_ISFIFO(os.fstat(sys.stdin.fileno()).st_mode)
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

    if input_filter_function:
        if verbose:
            ic(random)
        iterator = filtergen(iterator=iterator,
                             filter_function=input_filter_function,
                             verbose=verbose,
                             debug=debug,)
        if debug:
            ic(iterator)

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
                try:
                    string = string.decode('utf8')
                except UnicodeDecodeError as e:
                    if verbose:
                        ic(e)
                    ic(string)
                    raise e


        if debug:
            try:
                ic(len(string))
            except (TypeError, AttributeError):
                pass    # need to be able to iterate over arb objects

        yield string
        lines_output += 1


@increment_debug
def enumerate_input(*,
                    iterator,
                    skip: Optional[int],
                    head: Optional[int],
                    tail: Optional[int],
                    verbose: bool,
                    debug: bool,
                    null: bool = False,
                    loop: bool = False,
                    disable_stdin: bool = False,
                    random: bool = False,
                    dont_decode: bool = False,
                    progress: bool = False,
                    input_filter_function: Optional[object] = None,
                    ):

    if progress and (verbose or debug):
        raise ValueError('--progress and --verbose/--debug are mutually exclusive')
    if verbose:
        ic(skip, head, tail, null, loop, disable_stdin, random, dont_decode, progress)

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
                                   verbose=verbose,
                                   input_filter_function=input_filter_function,)
    start_time = time.time()
    if debug:
        ic(inner_iterator)

    for index, thing in enumerate(inner_iterator):
        if progress:
            if index % 100 == 0:
                items_total = index + 1
                time_running = time.time() - start_time
                items_per_second = int(items_total / time_running)
                #print(index + 1, file=sys.stderr, end='\r')
                print(items_total, items_per_second, file=sys.stderr, end='\r')
        yield index, thing
    if progress:
        print("", file=sys.stderr)
