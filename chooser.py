#!/usr/bin/env python

import urwid
import sys
import os
import string


def getTerminalSize():
    """ taken from
    http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python/566752#566752
    by user Johannes Weiss http://stackoverflow.com/users/55925/johannes-weiss
    """
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            import struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
                               '1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (env['LINES'], env['COLUMNS'])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])


class SelText(urwid.Text):
    """
Selectable Text with an aditional href varibale
"""
    def __init__(self, text):
        urwid.Text.__init__(self, text)

    def selectable(self):
        """needs to be implemented"""
        return True

    def keypress(self, _, key):
        """needs to be implemented"""
        return key


class SelectedButton(Exception):
    def __init__(self, exit_token=None):
        Exception.__init__(self)
        self.exit_token = exit_token


class Selected(Exception):
    """
    used for signalling that an item was chosen in urwid
    """
    pass


def select_entry(names, width=80):
    """interactive href selector (urwid based)

    returns: href
    return type: string
    """
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
    show_key = urwid.Text(u"", wrap='clip')
    head = urwid.AttrMap(show_key, 'header')
    top = urwid.Frame(listbox, head)

    def show_all_input(input, raw):
        """used for urwid test
        to be removed
        """
        show_key.set_text(u"Pressed: " + u" ".join([
            unicode(i) for i in input]))
        return input

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
                          input_filter=show_all_input,
                          unhandled_input=keystroke)
    try:
        loop.run()
    except Selected:
        return names[listbox.get_focus()[1]]

##################################################
width, height = getTerminalSize()

auswahl = sys.stdin.read()


# save old stdout and in
old_out = sys.__stdout__
old_in = sys.__stdin__

sys.__stdout__ = sys.stdout = open('/dev/tty', 'wb')
sys.__stdin__ = sys.stdin = open('/dev/tty')
os.dup2(sys.stdin.fileno(), 0)


def get_lengths(auswahl):
    return map(max, zip(*[map(len, one) for one in auswahl]))

# main work is done here
width = 180 / 3
auswahl = auswahl.split('\n')
auswahl = auswahl[:-1]
auswahl = [one.split('\t') for one in auswahl]
laengen = get_lengths(auswahl)

auswahl = [[string.ljust(s[:lange - 1], lange) for s, lange in zip(wahl, laengen)] for wahl in auswahl]

auswahl = [''.join(elemente) for elemente in auswahl]
wahl = select_entry(auswahl)

#restore old stdout
sys.stdin.close()
sys.stdout.close()
sys.__stdout__ = sys.stdout = old_out
sys.__stdin__ = sys.stdin = old_in

# print chosen string
print(wahl + '\n')
print langen
