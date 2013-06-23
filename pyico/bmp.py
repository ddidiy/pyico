#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

# pyico BMP support.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

import struct

import binary


BITMAPFILEHEADER_SIZE = 14
BITMAPINFOHEADER_SIZE = 40
HEADERS_SIZE = BITMAPFILEHEADER_SIZE + BITMAPINFOHEADER_SIZE


class Bmp( object ):


  def __init__( self ):
    self._width_n = 0
    self._height_n = 0
    self._bpp_n = 0
    self._resCx_n = 0
    self._resCy_n = 0
    ##  Colors in palette.
    self._colors_n = 0
    ##  List of (r, g, b) tuples.
    self._palette_l = []
    ##  Two-dimenshional array. If |self._bpp_n| <= 8, contains indexes
    ##  of colors in |self._palette_l|, otherwise contains (r,g,b,a) tuples.
    self._pixels_l = []
    ##  Two-dimenshional array, 1 is transparent.
    self._alpha_l = []


  ##x Decodes BMP information from .ICO file and stores it in internal
  ##  representation.
  def fromIco( self, s_data ):

    oReader = binary.Reader( s_data )
    ##  Read BITMAPINFOHEADER and place data into object private fields.
    self._readBitmapHeader( oReader )
    self._readPalette( oReader )
    self._readPixels( oReader )

    ##  Since .bmp file don't have notion of transparency, replace some
    ##  colors with violet to mark as transparent. It's not needed for
    ##  |32| bit images since they already have alpha as |4|-th byte in
    ##  each pixel.
    if self._bpp_n < 32:

      self._readAlpha( oReader )
      nTransparent = self._defineTransparentColor()

      ##  Actual color replacement.
      for i in range( self._height_n ):
        for j in range( self._width_n ):
          if not 0 == self._alpha_l[ i ][ j ]:
            if self._bpp_n <= 8:
              self._pixels_l[ i ][ j ] = nTransparent
            else:
              nAlpha = self._pixels_l[ i ][ j ][ 3 ]
              self._pixels_l[ i ][ j ] = (0xFF, 0, 0xFF, nAlpha)


  ##x Decodes BMP information from uncompressed .BMP file and stores it in
  ##  internal representation.
  def fromBmp( self, s_data ):
    pass


  ##  Evaluates to binary representation of loaded image that can be stored
  ##  inside .ICO file. |width|, |height| etc can be used to construct
  ##  information section in ICO file.
  def toIco( self ):
    pass


  ##  Evaluates to binary representation of loaded image that can be
  ##  saved as .BMP file.
  def toBmp( self ):

    sData = ''
    sData += self._createFileHeader()
    sData += self._createPalette()
    sData += self._createPixels()
    return sData


  def _readBitmapHeader( self, o_reader ):

    assert BITMAPINFOHEADER_SIZE == o_reader.read( '<I' )
    self._width_n, self._height_n = o_reader.read( '<II' )
    ##! Height counts alpha channel mask as a separate image.
    self._height_n = self._width_n
    ##  Number of color planes.
    assert 1 == o_reader.read( '<H' )
    self._bpp_n = o_reader.read( '<H' )
    assert self._bpp_n in [ 1, 4, 8, 16, 24, 32 ]
    nCompression = o_reader.read( '<I' )
    ##! Only uncompressed images are supported.
    assert 0 == nCompression

    nImageSize = o_reader.read( '<I' )
    ##  Bytes in horizontal line in image.
    self._lineSize_n = ((self._width_n * self._bpp_n) / 8) or 1
    ##! Lines are 4-byte aligned.
    self._lineSize_n += self._lineSize_n % 4
    ##  Can be 0 for uncompressed bitmaps.
    assert 0 == nImageSize or self._lineSize_n * self._height_n == nImageSize

    self._resCx_n, self._resCy_n = o_reader.read( '<ii' )
    self._colors_n = o_reader.read( '<I' )
    if 0 == self._colors_n and self._bpp_n <= 8:
      self._colors_n = pow( 2, self._bpp_n )
    ##  Important colors in palette.
    o_reader.read( '<I' )


  def _readPalette( self, o_reader ):

    sPalette = o_reader.readArray( self._colors_n * 4 )
    self._palette_l = [ (0, 0, 0) for i in range( self._colors_n ) ]
    for i in range( self._colors_n ):
      r, g, b, _ = struct.unpack( '!BBBB', sPalette[ i * 4 : i * 4 + 4 ] )
      self._palette_l[ i ] = (r, g, b)


  def _readAlpha( self, o_reader ):

    ##  Bytes in horizontal line in alpha mask.
    nAlphaLineSize = (self._width_n / 8) or 1
    ##! Lines are 4-byte aligned.
    nAlphaLineSize = nAlphaLineSize  % 4
    sAlpha = o_reader.readArray( nAlphaLineSize * self._height_n )

    nSide = self._width_n
    self._alpha_l = [ [ 0 for x in range( nSide ) ] for y in range( nSide ) ]
    for i in range( nSide ):
      for j in range( nSide ):
        nOffsetInBytes = i * nAlphaLineSize + j / 8
        nOffsetInBits = i * nAlphaLineSize * 8 + j
        nByte = ord( sAlpha[ nOffsetInBytes ] )
        if not 0 == (nByte & (1 << (7 - (nOffsetInBits % 8)))):
          self._alpha_l[ i ][ j ] = 1
        else:
          self._alpha_l[ i ][ j ] = 0


  def _readPixels( self, o_reader ):

    sPixels = o_reader.readArray( self._lineSize_n * self._height_n )
    nSide = self._width_n
    self._pixels_l = [ [ 1 for x in range( nSide ) ] for y in range( nSide ) ]

    for i in range( nSide ):
      for j in range( nSide ):
        nOffsetInBytes = i * self._lineSize_n + (j * self._bpp_n) / 8
        nByte = ord( sPixels[ nOffsetInBytes ] )
        if 4 == self._bpp_n:
          nOffsetInBits = i * self._lineSize_n * 8 + j * self._bpp_n
          ##* Offset inside byte.
          nOffset = nOffsetInBits - nOffsetInBytes * 8
          if 0 == nOffset:
            self._pixels_l[ i ][ j ] = (nByte >> 4)
          if 4 == nOffset:
            self._pixels_l[ i ][ j ] = (nByte & 0xF)
        if 8 == self._bpp_n:
          self._pixels_l[ i ][ j ] = nByte
        if self._bpp_n >= 24:
          nRed = ord( sPixels[ nOffsetInBytes + 0 ] )
          nGreen = ord( sPixels[ nOffsetInBytes + 1 ] )
          nBlue = ord( sPixels[ nOffsetInBytes + 2 ] )
          nAlpha = 0
          if 32 == self._bpp_n:
            nAlpha = ord( sPixels[ nOffsetInBytes + 3 ] )
          self._pixels_l[ i ][ j ] = (nRed, nGreen, nBlue, nAlpha)


  def _defineTransparentColor( self ):
    if 4 == self._bpp_n:
      ##  In case of 16 colors use violet as transparent color, if
      ##  available.
      for i, gColor in enumerate( self._palette_l ):
        if (0xFF, 0, 0xFF) == gColor:
          return i
    ##  In case of 256 colors palette use color with index 255 as
    ##  transparent and change it's palette color to violet.
    if 8 == self._bpp_n:
      self._palette_l[ 0xFF ] = (0xFF, 0, 0xFF)
      return 0xFF


  def _createFileHeader( self ):
    return struct.pack( '<HIHHIIIIHHIIiiII',
      ##  .bmp Magic.
      struct.unpack( '<H', 'BM' )[ 0 ],
      ##  File size.
      HEADERS_SIZE + self._colors_n * 4 + self._lineSize_n * self._height_n,
      ##  Reserved.
      0,
      ##  Reserved.
      0,
      ##  Offset from beginning of file to pixel data.
      HEADERS_SIZE + self._colors_n * 4,
      BITMAPINFOHEADER_SIZE,
      self._width_n,
      self._height_n,
      1,
      self._bpp_n,
      ##  Uncompressed.
      0,
      self._lineSize_n * self._height_n,
      self._resCx_n,
      self._resCy_n,
      self._colors_n,
      ##  Important colors.
      self._colors_n )


  def _createPalette( self ):
    sData = ''
    for gColor in self._palette_l:
      sData += struct.pack( '!BBBB', * (list( gColor ) + [ 0 ]) )
    return sData


  def _createPixels( self ):
    sData = ''
    for nY in range( self._height_n ):
      lAccumulated = []
      for nX in range( self._height_n):
        if self._bpp_n <= 8:
          lAccumulated.append( self._pixels_l[ nY ][ nX ] )
          ##  Collected one or more bytes:
          if ((len( lAccumulated ) * self._bpp_n) / 8) > 0:
            nByte = 0
            for i, nColor in enumerate( lAccumulated ):
              nByte |= (nColor << (8 - self._bpp_n - self._bpp_n * i))
            lAccumulated = []
            sData += chr( nByte )
        elif 24 == self._bpp_n:
          gColor = self._pixels_l[ nY ][ nX ]
          sData += struct.pack( '!BBB', * list( gColor )[ : 3 ] )
        elif 32 == self._bpp_n:
          gColor = self._pixels_l[ nY ][ nX ]
          sData += struct.pack( '!BBBB', * gColor )
      nFill = self._lineSize_n - ((self._width_n * self._bpp_n) / 8 or 1)
      sData += '\x00' * nFill
    assert len( sData ) == self._lineSize_n * self._height_n
    return sData

