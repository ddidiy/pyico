#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pyico simple test.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

# Test.

import pyico

oIco = pyico.open( "test.ico" )
open( "out.ico", 'wb' ).write( oIco.data() )
oIco = pyico.open( "out.ico" )
# open( "out.bmp", 'wb' ).write( oIco.images_l[ 0 ].data_s )
# open( "out.ico", 'wb' ).write( oIco.data() )

"""
print( "size: {0} x {1}".format( * oImg.size_g ) )
ABOUT_MODE = { 'RGB': 'RGB', 'L': 'Grayscale', 'P': 'Indexed' }
print( "mode: {0}".format( ABOUT_MODE[ oImg.mode_s ] ) )
for oLayer in oImg.layers_l:
  print( "  Layer" )
  print( "  size: {0} x {1}".format( * oLayer.size_g ) )
  print( "  mode: {0}, alpha: {1}".format( oLayer.mode_s, oLayer.alpha_f ) )
"""

