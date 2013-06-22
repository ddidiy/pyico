#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

# pyico implementation.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

# Main library code.

import __builtin__, struct

class Ico( object ):


  def __init__( self ):
    self.images_l = []


class Image( object ):


  def __init__( self ):
    self.width_n = 0
    self.height_n = 0
    self.colors_n = 0
    self.planes_n = 0
    self.bpp_n = 0
    self.data_s = 0


  def __str__( self ):
    return "{width_n}x{height_n}x{bpp_n}".format( ** self.__dict__ )


class CReader( object ):


  def __init__( self, s_data ):
    self.data_s = s_data
    self.offset_n = 0
    self.offsets_l = []


  def read( self, s_format ):
    ABOUT = { '!': 0, '<': 0, 'B': 1, 'H': 2, 'I': 4, 'f': 4 }
    nLen = reduce( lambda x, y: x + y, [ ABOUT[ x ] for x in s_format ] )
    sSplice = self.data_s[ self.offset_n: self.offset_n + nLen ]
    gItems = struct.unpack( s_format, sSplice )
    self.offset_n += nLen
    return gItems if len( gItems ) > 1 else gItems[ 0 ]


  def readArray( self, n_len ):
    sSplice = self.data_s[ self.offset_n: self.offset_n + n_len ]
    self.offset_n += n_len
    return sSplice


  def push( self, n_newOffset ):
    self.offsets_l.append( self.offset_n )
    self.offset_n = n_newOffset


  def pop( self ):
    self.offset_n = self.offsets_l.pop()


class ReaderIco( CReader ):


  def readImage( self ):

    oImage = Image()
    oImage.width_n = self.read( '<B' )
    if 0 == oImage.width_n:
      oImage.width_n = 256
    oImage.height_n = self.read( '<B' )
    if 0 == oImage.height_n:
      oImage.height_n = 256
    oImage.colors_n = self.read( '<B' )
    assert 0 == self.read( '<B' )
    oImage.planes_n = self.read( '<H' )
    assert oImage.planes_n in [ 0, 1 ]
    oImage.bpp_n = self.read( '<H' )
    nData = self.read( '<I' )
    nOffset = self.read( '<I' )

    self.push( nOffset )
    oImage.data_s = self.readArray( nData )
    self.pop()

    return oImage


def open( fp, mode = 'r' ):
  assert 'r' == mode
  with __builtin__.open( fp, mode ) as oFile:
    oReader = ReaderIco( oFile.read() )
  oIco = Ico()

  ##  Read header
  assert 0 == oReader.read( '<H' )
  assert 1 == oReader.read( '<H' )
  nImages = oReader.read( '<H' )
  assert nImages > 0

  for i in range( nImages ):
    oImage = oReader.readImage()
    print( oImage )
    oIco.images_l.append( oImage )

  return oIco

