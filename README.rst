=====
pyico
=====

A simple python script that can read and write windows .ico files. Data is
manipulated as RAW BMP or PNG, other graphic processing library like PIL can
be used to manipulate data as image.

Why?
====

I can find only code that can read .ico files (Win32IconImagePlugin.py) and
it can't be installed via pypi. This code can read and write .ico files, see
test.py for demonstration. I use it to automate high-DPI icons creation
from vector source.

