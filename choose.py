import re
import shutil
import sys
import tty
import termios

CTRL = '\x1b'
RESET = CTRL + '[0m'
COLOR = CTRL + '[31m'
HOME = CTRL + '[H'
ALTERNATE_BUFFER_ON = CTRL + '7' + CTRL + '[?47h'
ALTERNATE_BUFFER_OFF = CTRL + '[?47l' + CTRL + '8'
SHOW_CURSOR = CTRL + '[?25h'
HIDE_CURSOR = CTRL + '[?25l'

KEYS = {
    '[A': 'up',
    '[B': 'down',
}


firstline = 'Navigate with ↑ and ↓, `return` exits and prints currently selected line'


class Console():
    def __enter__(self):
        print(HIDE_CURSOR)
        print(ALTERNATE_BUFFER_ON)

    def __exit__(self, exc_type, exc_value, traceback):
        print(SHOW_CURSOR)
        print(ALTERNATE_BUFFER_OFF)


def get_data(filename):
    with open(filename) as f:
        data = f.readlines()
    return [line.strip('\n') for line in data]


def get_input():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch = KEYS.get(sys.stdin.read(2))
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def out(line, width, color='', newline=True):
    line = line[:width].ljust(width)
    if color:
        line = color + line + RESET
    if newline:
        line = line + '\n'
    sys.stderr.write(line)


def render(data, width, height, focus, lastline):
    framecolor = CTRL + '[44m' + CTRL + '[37m'
    highlight = CTRL + '[47m' + CTRL + '[34m'
    out(firstline, width, color=framecolor)
    if focus + height - 2 > len(data):
        lower = max(0, len(data) - height)
    else:
        lower = focus

    for lineno in range(lower, lower + height - 2):
        try:
            color = highlight if lineno == focus else ''
            out(data[lineno], width, color)
        except IndexError:
            out('', width)
    out(lastline, width, color=framecolor, newline=False)
    sys.stderr.flush()


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


def filter_regex(data, string):
    regex = re.compile(string)
    return [line for line in data if regex.search(line)]

if __name__ == '__main__':
    data = get_data(sys.argv[1])[:]
    width, height = shutil.get_terminal_size()
    with Console():
        focus = 0
        filter_mode = 0
        filters = [
            (filter_fuzzy, 'fuzzy'),
            (filter_regex, 'regex'),
        ]

        search_term, last_search_term = '', ''
        mydata = data
        rprint = False
        while True:
            filter_fun = filters[filter_mode][0]
            if last_search_term != search_term:
                mydata = filter_fun(data, search_term)
                last_search_term = search_term
            if search_term:
                lastline = '({}) Searching for: {}'.format(filters[filter_mode][1], search_term)
            else:
                lastline = 'Start typeing for search, ctrl-t for switching search mode'
            render(mydata, width, height, focus, lastline=lastline)
            key = get_input()
            if key in ['up', 'down']:
                focus = adjust_focus(mydata, focus, key)
            elif key in ['\r']:
                rprint = data[focus]
                break
            elif key in ['\x7f']:  # backspace
                search_term = search_term[:-1]
            elif key in ['\x03']:  # ctrl-c
                break
            elif key in ['\x14']:  # ctrl-t, bad-choice
                filter_mode = (filter_mode + 1) % len(filters)
            elif key is not None:
                search_term = search_term + key
    if rprint:
        print(rprint)
    sys.exit(0)
