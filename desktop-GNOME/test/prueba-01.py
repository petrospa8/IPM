#!/usr/bin/env python3
# coding: utf-8

import pyatspi
import os
import subprocess
from time import sleep

from pathlib import Path

# Lanzar ../ipm-p1.py
script_path = Path(__file__).parent.parent.absolute()
os.system('cd ' + str(script_path) + ' && ./ipm-p1.py &')
print(str(script_path))

sleep(1)

desktop = pyatspi.Registry.getDesktop(0)
for app in desktop:
    print(app.name)
    if app.name == 'ipm-p1.py':
        ipm = app

print(ipm.name)

frame = ipm[0]
panel = frame[0]   # Header
scroll = frame[1]  # Scroll pane
table = scroll[0]

table[10].queryComponent().grabFocus()
sleep(1)
pyatspi.Registry.generateKeyboardEvent(36, None, pyatspi.KEY_PRESSRELEASE)

new_scroll = frame[1]

children = len(new_scroll[0][0])
if children == 26:
    print('Test passed')
else:
    print('Error: children should be 26 and are ' + children)
