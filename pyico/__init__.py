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
    self.file_s = ''


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


  ##x Adds new image from uncompressed .bmp file content.
  def addFromBmp( self,
    ##i Image data as loaded from |.bmp| file.
    s_data,
    ##i If specified, image's 'bits per pixel' value will be converted
    ##  to specified. Used if image is programmatically generated (for
    ##  expample, via PIL) and generator can't produce required bits per
    ##  pixel for .bmp format (for example, PIL can't create 4 bits per
    ##  pixel BMP).
    n_bpp = None ):

    oBmp = bmp.Bmp()
    oBmp.fromBmp( s_data, n_bpp )
    oImage = Image()
    oImage.initFromBmp( oBmp )
    self.images_l.append( oImage )


  ##x Adds new image from raw 32-bit data in 'RGBA' fromat, first 4
  ##  bytes are top-left corner.
  def addFromRaw( self, s_data, n_width, n_height, n_bpp ):
    assert 32 == n_bpp

    oBmp = bmp.Bmp()
    oBmp.fromRaw( s_data, n_width, n_height, n_bpp )
    oImage = Image()
    oImage.initFromBmp( oBmp )
    self.images_l.append( oImage )


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


  def initFromBmp( self, o_bmp ):
    self.width_n = o_bmp.width()
    self.height_n = o_bmp.height()
    self.colors_n = o_bmp.colors()
    self.planes_n = 1
    self.bpp_n = o_bmp.bpp()
    self.data_s = o_bmp.toBmp()


  def alpha( self ):
    oBmp = bmp.Bmp()
    oBmp.fromBmp( self.data_s )
    return oBmp.alpha()


  def __str__( self ):
    return "IMAGE: {width_n}x{height_n}x{bpp_n}".format( ** self.__dict__ )

  def __repr__( self ):
    return self.__str__()


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
      ##! Otherwrite image header data from |BMP| file structure, since
      ##  it can be corrpupted: for example, |bpp| value can be 0.
      oImage.initFromBmp( oBmp )

    return oImage


class WriterIco( binary.Writer ):


  def writeImage( self, o_image ):

    oBmp = bmp.Bmp()
    oBmp.fromBmp( o_image.data_s )
    ##  User can assign new bitmap, so reload image parameters from it.
    o_image.initFromBmp( oBmp )

    nWidth = o_image.width_n
    assert nWidth <= 256
    if 256 == nWidth:
      nWidth = 0
    self.write( '<B', nWidth )

    nHeight = o_image.width_n
    assert nHeight <= 256
    if 256 == nHeight:
      nHeight = 0
    self.write( '<B', o_image.height_n )
    if 256 == o_image.colors_n:
      o_image.colors_n = 0
    self.write( '<B', o_image.colors_n )
    self.write( '<B', 0 )
    self.write( '<H', o_image.planes_n )
    self.write( '<H', o_image.bpp_n )

    self.writeSize( '<I', o_image.index_n )
    self.writeOffset( '<I', o_image.index_n )

    self.writeArrayEnd( oBmp.toIco(), n_id = o_image.index_n )


def open( fp, mode = 'r' ):
  assert 'r' == mode
  with __builtin__.open( fp, mode + 'b' ) as oFile:
    oReader = ReaderIco( oFile.read() )
  oIco = Ico()
  oIco.file_s = fp

  ##  Read header
  assert 0 == oReader.read( '<H' )
  assert 1 == oReader.read( '<H' )
  nImages = oReader.read( '<H' )
  assert nImages > 0

  for i in range( nImages ):
    oImage = oReader.readImage()
    oIco.images_l.append( oImage )

  return oIco

