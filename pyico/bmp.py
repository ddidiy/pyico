#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

# pyico BMP support.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

class Bmp( object ):


  def __init__( self ):
    pass


  ##x Decodes BMP information from .ICO file and stores it in internal
  ##  representation.
  def fromIco( self, arg ):
    pass


  ##x Decodes BMP information from uncompressed .BMP file and stores it in
  ##  internal representation.
  def fromBmp( self, arg ):
    pass


  ##  Evaluates to binary representation of loaded image that can be stored
  ##  inside .ICO file. |width|, |height| etc can be used to construct
  ##  information section in ICO file.
  def toIco( arg ):
    pass


  ##  Evaluates to binary representation of loaded image that can be
  ##  saved as .BMP file.
  def toBmp( arg ):
    pass

