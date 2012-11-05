#!/usr/bin/env python

import urwid
import sys
import os


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


def select_entry(names):
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


auswahl = sys.stdin.read()
auswahl = auswahl.split('\n')
sys.__stdin__.close()
sys.__stdin__ = sys.stdin = open('/dev/tty')
os.dup2(sys.stdin.fileno(), 0)
wahl = select_entry(auswahl)
sys.stderr.write(wahl + '\n')
