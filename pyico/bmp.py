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
    ##  Width of single line in image data, in bytes.
    self._lineSize_n = 0
    ##  List of (r, g, b) tuples.
    self._palette_l = []
    ##  Two-dimenshional array. If |self._bpp_n| <= 8, contains indexes
    ##  of colors in |self._palette_l|, otherwise contains (r,g,b,a) tuples.
    self._pixels_l = []
    ##  Two-dimenshional array, 1 is transparent.
    self._alpha_l = []


  def width( self ):
    return self._width_n


  def height( self ):
    return self._height_n


  def colors( self ):
    return self._colors_n


  def bpp( self ):
    return self._bpp_n


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
    ##! 32-bit .BMP has alpha channel written into every 4-th byte. Windows
    ##  will not be able to display it, but programs like GIMP will.
    if self._bpp_n < 32:

      self._readAlpha( oReader )
      if self._bpp_n <= 8:
        nTransparent = self._defineTransparentColor()
        assert nTransparent is not None

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
  def fromBmp( self, s_data, n_bpp = None ):

    oReader = binary.Reader( s_data )
    ##  Skip BITMAPFILEHEADER
    oReader.readArray( BITMAPFILEHEADER_SIZE )
    ##  Read BITMAPINFOHEADER and place data into object private fields.
    self._readBitmapHeader( oReader )
    self._readPalette( oReader )
    self._readPixels( oReader )
    ##  Override bits per pixels value if required (see caller for details).
    if n_bpp is not None and n_bpp < self._bpp_n:
      assert n_bpp <= 8
      self._bpp_n = n_bpp
      self._colors_n = pow( 2, n_bpp )
      self._lineSize_n = self._lineSize( self._width_n, self._bpp_n )
      self._palette_l = self._palette_l[ : pow( 2, n_bpp ) ]
      for i in range( self._height_n ):
        for j in range( self._width_n ):
          assert self._pixels_l[ i ][ j ] < pow( 2, n_bpp )
    ##  Create alpha mask based on image colors.
    nSide = self._width_n
    self._alpha_l = [ [ 0 for x in range( nSide ) ] for y in range( nSide ) ]
    nTransparent = self._defineTransparentColor()
    for i in range( nSide ):
      for j in range( nSide ):
        if self._bpp_n <= 8:
          if self._pixels_l[ i ][ j ] == nTransparent:
            self._alpha_l[ i ][ j ] = 1
          else:
            self._alpha_l[ i ][ j ] = 0
        if 24 == self._bpp_n:
          if (0xFF, 0, 0xFF) == self._pixels_l[ i ][ j ][ : 3 ]:
            self._alpha_l[ i ][ j ] = 1
          else:
            self._alpha_l[ i ][ j ] = 0
        if 32 == self._bpp_n:
          if self._pixels_l[ i ][ j ][ 3 ] < 128:
            self._alpha_l[ i ][ j ] = 1
          else:
            self._alpha_l[ i ][ j ] = 0


  ##  Constructs image from raw 32-bit data in 'RGBA' fromat, first 4
  ##  bytes are top-left corner.
  def fromRaw( self, s_data, n_width, n_height, n_bpp ):
    assert 32 == n_bpp

    self._width_n = n_width
    self._height_n = n_height
    self._bpp_n = n_bpp
    self._resCx_n = 0
    self._resCy_n = 0
    self._colors_n = 0
    self._lineSize_n = self._lineSize( self._width_n, self._bpp_n )
    self._palette_l = []
    self._alpha_l = []
    nSide = self._width_n
    self._pixels_l = [ [ 0 for x in range( nSide ) ] for y in range( nSide ) ]
    for i in range( self._height_n ):
      for j in range( self._width_n ):
        self._pixels_l[ self._height_n - i - 1 ][ j ] = (
          ord( s_data[ (i * self._width_n + j) * 4 + 0 ] ),
          ord( s_data[ (i * self._width_n + j) * 4 + 1 ] ),
          ord( s_data[ (i * self._width_n + j) * 4 + 2 ] ),
          ord( s_data[ (i * self._width_n + j) * 4 + 3 ] ) )


  ##  Evaluates to binary representation of loaded image that can be stored
  ##  inside .ICO file. |width|, |height| etc can be used to construct
  ##  information section in ICO file.
  def toIco( self ):

    sData = ''
    sData += self._createBitmapHeader( f_ico = True )
    sData += self._createPalette()
    sData += self._createPixels()
    sData += self._createAlpha()

    return sData


  ##  Evaluates to binary representation of loaded image that can be
  ##  saved as .BMP file.
  def toBmp( self ):

    sData = ''
    sData += self._createFileHeader()
    sData += self._createBitmapHeader()
    sData += self._createPalette()
    sData += self._createPixels()
    return sData


  ##  Evaluates to 8-bit alpha array, first item is top-left corner.
  def alpha( self ):
    sAlpha = ''
    for i in range( self._height_n ):
      for j in range( self._width_n ):
        if 32 == self._bpp_n:
          sAlpha += chr( self._pixels_l[ self._height_n - i - 1 ][ j ][ 3 ] )
        else:
          if 1 == self._alpha_l[ self._height_n - i - 1 ][ j ]:
            sAlpha += chr( 0 )
          else:
            sAlpha += chr( 0xFF )
    return sAlpha


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
    self._lineSize_n = self._lineSize( self._width_n, self._bpp_n )
    ##  Can be 0 for uncompressed bitmaps.
    assert 0 == nImageSize or nImageSize >= self._lineSize_n * self._height_n

    self._resCx_n, self._resCy_n = o_reader.read( '<ii' )
    self._colors_n = o_reader.read( '<I' )
    if 0 == self._colors_n and self._bpp_n <= 8:
      self._colors_n = pow( 2, self._bpp_n )
    ##  Important colors in palette.
    o_reader.read( '<I' )


  def _createBitmapHeader( self, f_ico = False ):
    return struct.pack( '<IIIHHIIiiII',
      BITMAPINFOHEADER_SIZE,
      self._width_n,
      ##! Bitmaps in ICO contains 'AND mask', it's data is written after
      ##  pixel data. To indicate presence of this mask, image height is
      ##  doubled.
      ##! 32-bit images may skip 'AND mask', but it's a good pactice to keep
      ##  it for optimization reasons, bacward compatibility and tolerance to
      ##  programs that can't handle it's absence.
      self._height_n * 2 if f_ico else self._height_n,
      ##  Number of color planes.
      1,
      self._bpp_n,
      ##  Uncompressed.
      0,
      self._lineSize_n * self._height_n,
      self._resCx_n,
      self._resCy_n,
      self._colors_n,
      ##  Number of important colors.
      self._colors_n )


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
    nAlphaLineSize += self._padding( self._width_n, n_bpp = 1, n_align = 4 )
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
    if self._bpp_n <= 8:
      ##  Use violet as transparent color, if available.
      for i, gColor in enumerate( self._palette_l ):
        if (0xFF, 0, 0xFF) == gColor:
          return i
      ##  If not available, search for index that is not used in image.
      lColorsUsed = [ False ] * pow( 2, self._bpp_n )
      for i in range( self._height_n ):
        for j in range( self._width_n ):
          lColorsUsed[ self._pixels_l[ i ][ j ] ] = True
      for i in range( len( lColorsUsed ) ):
        if not lColorsUsed[ i ]:
          self._palette_l[ i ] = (0xFF, 0, 0xFF)
          return i
      else:
        assert False, "no free colors to use as transparent"
    return None


  def _createFileHeader( self ):
    return struct.pack( '<HIHHI',
      ##  .bmp Magic.
      struct.unpack( '<H', 'BM' )[ 0 ],
      ##  File size.
      HEADERS_SIZE + self._colors_n * 4 + self._lineSize_n * self._height_n,
      ##  Reserved.
      0,
      ##  Reserved.
      0,
      ##  Offset from beginning of file to pixel data.
      HEADERS_SIZE + self._colors_n * 4 )


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
      nPadding = self._padding( self._width_n, self._bpp_n, n_align = 4 )
      sData += '\x00' * nPadding
    assert len( sData ) == self._lineSize_n * self._height_n
    return sData


  def _createAlpha( self ):
    sData = ''
    for nY in range( self._height_n ):
      lAccumulated = []
      def accumulatedToData():
        nByte = 0
        for i, nAlpha in enumerate( lAccumulated ):
          if not 0 == nAlpha:
            nByte |= (1 << (7 - i))
        return chr( nByte )
      for nX in range( self._width_n):
        lAccumulated.append( self._alpha_l[ nY ][ nX ] )
        ##  Collected one byte?
        if 8 == len( lAccumulated ):
          sData += accumulatedToData()
          lAccumulated = []
      if lAccumulated:
        sData += accumulatedToData()
      nPadding = self._padding( self._width_n, n_bpp = 1, n_align = 4 )
      sData += '\x00' * nPadding
    return sData


  ##x Number of bytes to add for image line with |n_width| amount of
  ##  pixels, |n_bpp| bits per pixel so it will be aligned at |n_align|
  ##  bytes.
  def _padding( self, n_width, n_bpp, n_align ):
    nPaddingBits = n_align * 8 - (n_width * n_bpp) % (n_align * 8)
    if nPaddingBits == n_align * 8:
      nPaddingBits = 0
    return nPaddingBits / 8


  def _lineSize( self, n_width, n_bpp ):
    ##  Bytes in horizontal line in image.
    nLineSize = ((n_width * n_bpp) / 8) or 1
    ##! Lines are 4-byte aligned.
    nLineSize += self._padding( n_width, n_bpp, n_align = 4 )
    return nLineSize

