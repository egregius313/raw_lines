#!/usr/bin/env python
"""
raw_lines.py

A basic utility to figure out how many executable lines of code
there are in a Python file.

Usage:
  raw_lines.py [options] <file>...

Options:
   -c, --count                       Counts the number of raw lines.
   -o=<out-file>, --out=<out-file>   Writes output to <out-file>.
   -l, --library                     Removes all entry point code.
   -h, --help                        Show help/usage page.
   --version                         Show the version number and exit.
"""

import re
from typing import Iterator

import docopt


BLOCK_STRING_DELIMITERS = re.compile('["\']{3}')

STATEMENTS = [
    'class',
    'def',
    'elif',
    'else',
    'for',
    'if',
    'while',
]

_STATEMENT_PATTERN = re.compile(
    '|'.join('(%s)' % stmt for stmt in STATEMENTS)
)

DEFINITION_STATEMENTS = ('class', 'def')
SPACES = 4


def block_statement(line):
    return _STATEMENT_PATTERN.match(line.lstrip())


def is_definition(line: str) -> bool:
    """Whether or not a line is a 
    definition statement.
    """
    return any(line.strip().startswith(definition)
               for definition in DEFINITION_STATEMENTS)


def raw_lines(f_stream: Iterator[str]) -> Iterator[str]:
    """
    Process a stream of lines (any iterable of strings ending in '\n')
    and return an integer of the number of lines that are actually executable.
    """
    for line in iter(lambda: next(f_stream), ''):
        stripped_line = line.strip()
        if stripped_line == '' or stripped_line.startswith('#'):
            continue
        if is_definition(stripped_line):
            next_line = next(f_stream)
            block_quote = BLOCK_STRING_DELIMITERS.match(next_line.strip())
            if block_quote:
                quotes = block_quote.group()
                if next_line.count(quotes) != 2:
                    next_line = next(f_stream)
                    while quotes not in next_line:
                        next_line = next(f_stream)
                yield line
            else:
                yield line
                yield next_line
        else:
            yield line


def library(f_stream: Iterator[str]) -> Iterator[str]:
    """
    Reads a stream and removes all
    """
    entry_point = re.compile(r'if __name__ == ["\']__main__["\']:')
    indentation_level = 0
    INDENT = '    '
    for line in iter(lambda: next(f_stream), ''):
        if entry_point.match(line):
            indentation_level += 1
            next_line = next(f_stream)
            while (next_line.startswith(INDENT * indentation_level)
                   or next_line.strip() == ''):
                try:
                    next_line = next(f_stream)
                except StopIteration:
                    break
            indentation_level -= 1
        else:
            yield line


def count_lines(f_stream: Iterator[str]) -> Iterator[str]:
    """
    Return the number of lines in the file stream.
    """
    return sum(1 for _ in f_stream)


if __name__ == '__main__':
    import sys

    exit_code = 0
    arguments = docopt.docopt(__doc__, version='0.1')

    # Whether there is a file to be used, otherwise stdin becomes the file.
    using_file = bool(arguments.get('<file>'))

    if using_file:
        in_streams = []
        for file in arguments['<file>']:
            try:
                in_streams.append((file, open(file, 'r')))
            except FileNotFoundError:
                sys.stderr.write('raw_lines.py: %s: No such file or directory\n' % file)
                exit_code = 1
    else:
        in_streams = [('-', sys.stdin)]

    out_stream = open(arguments['--out'], 'w') if arguments.get('--out') else sys.stdout

    with out_stream:
        for file, in_stream in in_streams:
            lines = raw_lines(in_stream)

            if arguments.get('--library'):
                lines = library(lines)

            if arguments.get('--count'):
                out_stream.write('{count:d} {file}'.format(
                    count=count_lines(lines),
                    file=file,
                    ).strip() + '\n'
                )
            else:
                for line in lines:
                    out_stream.write(line)

    sys.exit(exit_code)
