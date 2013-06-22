#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

# pyico implementation.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

# Main library code.

import __builtin__, struct
import PIL.BmpImagePlugin
import StringIO

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
    ##  if set to |True|, data is in compressed |png| format alongside
    ##  with header.
    self.png_f = False


  def __str__( self ):
    return "{width_n}x{height_n}x{bpp_n}".format( ** self.__dict__ )


class Reader( object ):


  def __init__( self, s_data ):
    self.data_s = s_data
    self.offset_n = 0
    self.offsets_l = []


  def read( self, s_format ):
    ABOUT = { '!': 0, '<': 0, 'B': 1, 'H': 2, 'I': 4, 'i': 4, 'f': 4 }
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


class ReaderIco( Reader ):


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
      self._decodeBmp( oImage )

    return oImage


  ##  Reads .ico version of BMP file from arg.data_s (with doubled height,
  ##  'AND' transparency image etc) and writes back a BMP file data so
  ##  it can be writen back to valid .bmp file.
  def _decodeBmp( self, arg ):

    BITMAPFILEHEADER_SIZE = 14
    BITMAPINFOHEADER_SIZE = 40
    HEADERS_SIZE = BITMAPFILEHEADER_SIZE + BITMAPINFOHEADER_SIZE

    oReader = Reader( arg.data_s )
    assert BITMAPINFOHEADER_SIZE == oReader.read( '<I' )
    nWidth, nHeight = oReader.read( '<II' )
    ##  Number of color planes.
    assert 1 == oReader.read( '<H' )
    nBpp = oReader.read( '<H' )
    assert nBpp in [ 1, 4, 8, 16, 24, 32 ]
    nCompression = oReader.read( '<I' )
    nImageSize = oReader.read( '<I' )
    ##  Can be 0 for uncompressed bitmaps.
    if 0 == nImageSize:
      nLineSize = (nWidth / nBpp)
      ##  Rows are 4-byte aligned.
      nLineSize += nLineSize % 4
      nImageSize = nLineSize * nHeight
    nResolutionCx, nResolutionCy = oReader.read( '<ii' )
    nColorsInPalette = oReader.read( '<I' )
    if 0 == nColorsInPalette and nBpp <= 8:
      nColorsInPalette = pow( 2, 4 )
    nColorsInPaletteImportant = oReader.read( '<I' )

    sPalette = oReader.readArray( nColorsInPalette * 4 )
    sPixels = oReader.readArray( nImageSize )
    nAlphaSize = 0
    sAlpha = ""
    if nBpp < 32:
      nAlphaSize = ((nWidth * nHeight) / nBpp) or 1
      sAlpha = oReader.readArray( nAlphaSize )

    arg.data_s = struct.pack( '<HIHHIIIIHHIIiiII',
      ##  .bmp Magic.
      struct.unpack( '<H', 'BM' )[ 0 ],
      ##  File size.
      HEADERS_SIZE + nColorsInPalette * 4 + nImageSize,
      ##  Reserved.
      0,
      ##  Reserved.
      0,
      ##  Offset from beginning of file to pixel data.
      HEADERS_SIZE + nColorsInPalette * 4,
      40,
      ##! Remove "AND mask" with transparency info.
      nWidth, nHeight / 2,
      1,
      nBpp,
      nCompression,
      nImageSize,
      nResolutionCx,
      nResolutionCy,
      nColorsInPalette,
      nColorsInPaletteImportant ) + sPalette + sPixels


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
    print( oImage )
    oIco.images_l.append( oImage )

  return oIco

