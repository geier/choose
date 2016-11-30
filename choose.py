#!/usr/bin/env python3
# encoding: utf-8
import argparse
import re
import subprocess
import shutil
import sys
import tty
import termios


if sys.version_info.major < 3:
    print('This program is not compatible with python 2. Sorry')
    sys.exit(99)


ESC = '\x1b'
RESET = ESC + '[0m'
COLOR = ESC + '[31m'
HOME = ESC + '[H'
ALTERNATE_BUFFER_ON = ESC + '7' + ESC + '[?47h'
ALTERNATE_BUFFER_OFF = ESC + '[?47l' + ESC + '8'
SHOW_CURSOR = ESC + '[?25h'
HIDE_CURSOR = ESC + '[?25l'

ESCKEYS = {
    '[A': 'up',
    '[B': 'down',
}

MAPPINGS = {
    '\x0e': 'down',  # ctrl+n
    '\x10': 'up',  # ctrl+p
    '\x04': 'screen down',  # ctrl+d
    '\x15': 'screen up',  # ctrl+u
}


firstline = 'Navigate with ↑ and ↓, `return` exits and prints currently selected line'


class Console():
    def __enter__(self):
        self.old_out = sys.stdout
        self.old_in = sys.stdin
        sys.__stdout__ = sys.stdout = open('/dev/tty', 'w')
        sys.__stdin__ = sys.stdin = open('/dev/tty', 'r')
        self.fd_stdin = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd_stdin)
        tty.setcbreak(self.fd_stdin)

        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.write(ALTERNATE_BUFFER_ON)

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.write(ALTERNATE_BUFFER_OFF)
        sys.stdout.flush()
        termios.tcsetattr(self.fd_stdin, termios.TCSADRAIN, self.old_settings)
        sys.__stdout__ = sys.stdout = self.old_out
        sys.__stdin__ = sys.stdin = self.old_in


def get_input():
    ch = sys.stdin.read(1)
    ch = MAPPINGS.get(ch, ch)
    # TODO use select to check if there is another character entered
    if ch == ESC:
        ch = ESCKEYS.get(sys.stdin.read(2))
    return ch


def out(line, width, color=''):
    line = line[:width].ljust(width)
    if color:
        line = color + line + RESET
    sys.stdout.write(line)


def render(data, width, height, focus, lastline):
    framecolor = ESC + '[44m' + ESC + '[37m'
    highlight = ESC + '[47m' + ESC + '[34m'

    sys.stdout.write(ESC + '[1;1H')
    out(firstline, width, color=framecolor)

    if focus + height - 2 > len(data):
        lower = max(0, len(data) - height + 2)
    else:
        lower = focus

    for term_line_no, data_line_no in enumerate(range(lower, lower + height - 1), 2):
        sys.stdout.write(ESC + '[{};1H'.format(term_line_no))
        try:
            color = highlight if data_line_no == focus else ''
            out(data[data_line_no], width, color)
        except IndexError:
            out('', width)
    sys.stdout.write(ESC + '[{};1H'.format(term_line_no))
    out(lastline, width, color=framecolor)
    sys.stdout.flush()


def adjust_focus(data, focus, key):
    if key == 'down' and focus < len(data) - 1:
        return focus + 1
    elif key == 'up' and not focus == 0:
        return focus - 1
    else:
        return focus


def filter_fuzzy(data, string):
    regex = re.compile('.*'.join(string), re.I)
    return [line for line in data if regex.search(line)]


def filter_substring(data, string):
    regex = re.compile('.*{}.*'.format(string), re.I)
    return [line for line in data if regex.search(line)]


def filter_regex(data, string):
    regex = re.compile(string)
    return [line for line in data if regex.search(line)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Make choices on the command line.')
    parser.add_argument(
        '-e', '--execute',
        help=(
            'execute EXECUTE in the background when pressing enter, '
            '{} will be replaced by the selected string. '
            'Example: --execute "zathura {}"'
        )
    )
    args = parser.parse_args()

    mydata = data = [line.strip('\n') for line in sys.stdin.readlines()]
    with Console():
        focus, filter_mode = 0, 0
        filters = [
            (filter_fuzzy, 'fuzzy'),
            (filter_substring, 'substring'),
            (filter_regex, 'regex'),
        ]

        search_term, old_search_term = '', ''
        old_filter_mode = None
        while True:
            width, height = shutil.get_terminal_size()
            filter_fun = filters[filter_mode][0]
            if old_search_term != search_term or old_filter_mode != filter_mode:
                mydata = filter_fun(data, search_term)
                old_search_term = search_term
                old_filter_mode = filter_mode
                if focus > len(mydata):
                    focus = len(mydata) - 1
            if search_term:
                lastline = '({}) Searching for: {}'.format(filters[filter_mode][1], search_term)
            else:
                lastline = 'Start typing for search, ctrl-t for switching search mode'
            render(mydata, width, height, focus, lastline=lastline)
            key = get_input()
            if key in ['up', 'down']:
                focus = adjust_focus(mydata, focus, key)
            elif key in ['\r', '\n']:
                result = mydata[focus]
                if args.execute:
                    subprocess.Popen(args.execute.format(result).split(' '))
                else:
                    break
            elif key in ['\x7f']:  # backspace
                search_term = search_term[:-1]
            elif key in ['\x03']:  # ctrl-c
                break
            elif key in ['\x14']:  # ctrl-t, bad-choice
                old_filter_mode = filter_mode
                filter_mode = (filter_mode + 1) % len(filters)
            elif key is not None:
                search_term = search_term + key
    print(locals().get('result', ''))
    sys.exit(0)
