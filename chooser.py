#!/usr/bin/env python
"""simple chooser program

reads lines from stdin, lets user choose one line in an urwid (ncurses like
interface), prints it to stdout and exits. Input will be aligned to tabs '\t'
"""

import urwid
import sys
import os


def get_terminal_size():
    """ taken from
    http://stackoverflow.com/questions/566746/566752#566752
    by user Johannes Weiss http://stackoverflow.com/users/55925/johannes-weiss
    """
    env = os.environ

    def ioctl_GWINSZ(filedesc):
        try:
            import fcntl
            import termios
            import struct
            con_props = struct.unpack('hh', fcntl.ioctl(filedesc,
                                                        termios.TIOCGWINSZ,
                                                        '1234'))
        except IOError:
            return None
        return con_props
    con_props = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not con_props:
        try:
            filedesc = os.open(os.ctermid(), os.O_RDONLY)
            con_props = ioctl_GWINSZ(filedesc)
            os.close(filedesc)
        except IOError:
            pass
    if not con_props:
        try:
            con_props = (env['LINES'], env['COLUMNS'])
        except:
            con_props = (25, 80)
    return int(con_props[1]), int(con_props[0])


def select_entry(names, header_text=''):
    """interactive href selector (urwid based)

    returns: href
    return type: string
    """
    class SelText(urwid.Text):
        """Selectable Text, saving index"""
        def __init__(self, text):
            urwid.Text.__init__(self, text)

        @classmethod
        def selectable(cls):
            """needs to be implemented"""
            return True

        @classmethod
        def keypress(cls, _, key):
            """needs to be implemented"""
            return key

    class Selected(Exception):
        """
        used for signalling that an item was chosen in urwid
        """
        pass

    if len(names) is 1:
        return names[0]
    if names == list():
        return None
    name_list = list()
    for one in names:
        name_list.append(SelText(one))
    palette = [('header', 'white', 'black'),
               ('reveal focus', 'black', 'dark cyan', 'standout'), ]
    content = urwid.SimpleListWalker([
        urwid.AttrMap(w, None, 'reveal focus') for w in name_list])

    listbox = urwid.ListBox(content)
    header = urwid.Text(header_text, wrap='clip')
    head = urwid.AttrMap(header, 'header')
    top = urwid.Frame(listbox, head)

    def keystroke(input):
        """used for urwid test
        to be removed
        """
        if input == 'q':
            raise urwid.ExitMainLoop()
        if input is 'enter':
            listbox.get_focus()[0].original_widget
            raise Selected()

    loop = urwid.MainLoop(top, palette,
                          unhandled_input=keystroke)
    try:
        loop.run()
    except Selected:
        return listbox.get_focus()[1]


def do_it():
    width, _ = get_terminal_size()

    auswahl = sys.stdin.read()

    # save old stdout and in
    old_out = sys.__stdout__
    old_in = sys.__stdin__
    old_err = sys.__stderr__

    sys.__stdout__ = sys.stdout = open('/dev/tty', 'wb')
    sys.__stdin__ = sys.stdin = open('/dev/tty')
    os.dup2(sys.stdin.fileno(), 0)

    def get_lengths(auswahl):
        """return max lengths of strings in 'columns' """
        return map(max, zip(*[map(len, one) for one in auswahl]))

    # main work is done here
    auswahl = auswahl.split('\n')[:-1]  # last line is always empty
    orig_auswahl = auswahl
    auswahl = [one.split('\t') for one in auswahl]

    #make sure all have elements have the same number of elements
    number_elements = max([len(one) for one in auswahl])
    for ind, _ in enumerate(auswahl):
        while len(auswahl[ind]) < number_elements:
            auswahl[ind].append('')

    laengen = get_lengths(auswahl)
    number_columns = len(laengen)
    number_splits = number_columns - 1

    while sum(laengen) + number_splits > width:
        missing = width - sum(laengen) - number_splits
        number_offenders = 0
        for lang in laengen:
            if lang > width / number_columns + number_splits:
                number_offenders = number_offenders + 1
        for ind, lang in enumerate(laengen):
            if lang > width / number_columns + number_splits:
                laengen[ind] = laengen[ind] + missing / number_offenders
                break

    # set length of column[i] to length[i], either clip or extent
    auswahl = [[s[:lange].ljust(lange + 1) for s, lange in zip(wahl, laengen)] for wahl in auswahl]

    auswahl = [''.join(elemente) for elemente in auswahl]
    index = select_entry(auswahl,
                         header_text='Who do You want to call today?')

    #restore old stdout
    sys.stdout.flush()
    sys.stderr.flush()
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()
    sys.__stdout__ = sys.stdout = old_out
    sys.__stdin__ = sys.stdin = old_in
    sys.__stderr__ = sys.stderr = old_err
    # print chosen string
    print(orig_auswahl[index])


do_it()
