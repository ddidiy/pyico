#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pyico simple test.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

# Test.

import os
import pyico

oIco = pyico.open( 'test.ico' )
with open( 'out.ico', 'wb' ) as oFile:
  oFile.write( oIco.data() )
oIco = pyico.open( 'out.ico' )
with open( 'out.bmp', 'wb' ) as oFile:
  oFile.write( oIco.images_l[ 0 ].data_s )
oIco.images_l = []
oIco.addFromBmp( open( 'out.bmp', 'rb' ).read() )
with open( 'out.ico', 'wb' ) as oFile:
  oFile.write( oIco.data() )

