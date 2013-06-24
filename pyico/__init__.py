#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

# pyico implementation.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

# Main library code.

import __builtin__, struct
import PIL.BmpImagePlugin
import StringIO

import binary
import bmp

class Ico( object ):


  def __init__( self ):
    self.images_l = []
    self._writer_o = WriterIco()


  ##  Evaluates to binary data corresponding to this icon. It can be used
  ##  to write modified icon into file.
  def data( self ):
    self._writer_o.clear()
    self._writer_o.write( '<H', 0 )
    self._writer_o.write( '<H', 1 )
    self._writer_o.write( '<H', len( self.images_l ) )
    for i, oImage in enumerate( self.images_l ):
      oImage.index_n = i
      self._writer_o.writeImage( oImage )
    return self._writer_o.data()


class Image( object ):


  def __init__( self ):
    self.width_n = 0
    self.height_n = 0
    self.colors_n = 0
    self.planes_n = 0
    self.bpp_n = 0
    self.data_s = 0
    ##  if set to |True|, data is in compressed |png| format alongside
    ##  with header.
    self.png_f = False
    ##  0-based index of this image inside .ico. Used by writer to
    ##  distinguish images in order to correctly write offset/sizes.
    self.index_n = None


  def __str__( self ):
    return "{width_n}x{height_n}x{bpp_n}".format( ** self.__dict__ )


class ReaderIco( binary.Reader ):


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

    ##  .ico don't have any means to distinguish BMP and PNG data, so
    ##  PNG is detected by 8-byte signature.
    PNG_MAGIC = '\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
    if nData > 8 and oImage.data_s.startswith( PNG_MAGIC ):
      oImage.png_f = True
    else:
      oImage.png_f = False
      ##  Read .ico version of BMP file (with doubled height,
      ##  'AND' transparency image etc) and convert to a BMP file data so
      ##  it can be writen back to valid .bmp file.
      oBmp = bmp.Bmp()
      oBmp.fromIco( oImage.data_s )
      oImage.data_s = oBmp.toBmp()

    return oImage


class WriterIco( binary.Writer ):


  def writeImage( self, o_image ):

    oBmp = bmp.Bmp()
    oBmp.fromBmp( o_image.data_s )
    ##  User can assign new bitmap, so reload image parameters from it.
    o_image.width_n = oBmp.width()
    o_image.height_n = oBmp.height()
    o_image.colors_n = oBmp.colors()
    o_image.planes_n = 1
    o_image.bpp_n = oBmp.bpp()
    o_image.data_s = oBmp.toIco()

    nWidth = o_image.width_n
    assert nWidth <= 256
    if 256 == nWidth:
      nWidth = 0
    self.write( '<B', nWidth )

    nHeight = o_image.width_n
    assert nHeight <= 256
    if 256 == nHeight:
      nHeight = 0
    ##! Bitmaps in ICO contains 'AND mask', it's data is written after
    ##  pixel data. To indicate presence of this mask, image height is
    ##  doubled.
    ##! 32-bit images may skip 'AND mask', but it's a good pactice to keep
    ##  it for optimization reasons, bacward compatibility and tolerance to
    ##  programs that can't handle it's absence.
    self.write( '<B', o_image.height_n * 2 )
    if 256 == o_image.colors_n:
      o_image.colors_n = 0
    self.write( '<B', o_image.colors_n )
    self.write( '<B', 0 )
    self.write( '<H', o_image.planes_n )
    self.write( '<H', o_image.bpp_n )

    self.writeSize( '<I', o_image.index_n )
    self.writeOffset( '<I', o_image.index_n )

    self.writeArrayEnd( o_image.data_s, n_id = o_image.index_n )


def open( fp, mode = 'r' ):
  assert 'r' == mode
  with __builtin__.open( fp, mode + 'b' ) as oFile:
    oReader = ReaderIco( oFile.read() )
  oIco = Ico()

  ##  Read header
  assert 0 == oReader.read( '<H' )
  assert 1 == oReader.read( '<H' )
  nImages = oReader.read( '<H' )
  assert nImages > 0

  for i in range( nImages ):
    oImage = oReader.readImage()
    oIco.images_l.append( oImage )

  return oIco

