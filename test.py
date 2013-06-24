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
open( "out.bmp", 'wb' ).write( oIco.images_l[ 0 ].data_s )

