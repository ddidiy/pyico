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
    self.writer_o = Writer()


  ##  Evaluates to binary data corresponding to this icon. It can be used
  ##  to write modified icon into file.
  def data( self ):
    self.writer_o.clear()
    self.writer_o.write( '<H', 0 )
    self.writer_o.write( '<H', 1 )
    self.writer_o.write( '<H', len( self.images_l ) )
    for i, oImage in enumerate( self.images_l ):
      oImage.index_n = i
      self._addDataForImage( oImage )
    return self.writer_o.data()


  def _addDataForImage( self, arg ):

    nWidth = arg.width_n
    assert nWidth <= 256
    if 256 == nWidth:
      nWidth = 0
    self.writer_o.write( '<B', nWidth )

    nHeight = arg.width_n
    assert nHeight <= 256
    if 256 == nHeight:
      nHeight = 0
    self.writer_o.write( '<B', nWidth )

    self.writer_o.write( '<B', arg.colors_n )
    self.writer_o.write( '<B', 0 )
    self.writer_o.write( '<H', arg.planes_n )
    self.writer_o.write( '<H', arg.bpp_n )

    self.writer_o.writeOffset( '<I', arg.index_n )
    self.writer_o.writeSize( '<I', arg.index_n )

    self.writer_o.writeArrayEnd( arg.data_s, n_id = arg.index_n )


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


class Writer( object ):


  def __init__( self ):
    self.chunks_l = []


  def data( self ):
    sData = ""

    ##  Data that has 'end' flag must be written after data without it.
    self.chunks_l = [ o for o in self.chunks_l if not o[ 'end_f' ] ] + \
      [ o for o in self.chunks_l if o[ 'end_f' ] ]

    ##  Calculate sizes and offsets of all data, so items marked as
    ##  'size' and 'offset' can be assigned correct values.
    nOffset = 0
    for mChunk in self.chunks_l:
      if mChunk[ 'type_s' ] in [ 'offset', 'size' ]:
        mChunk[ 'size_n' ] = len( struct.pack( mChunk[ 'format_s' ], 0 ) )
      else:
        mChunk[ 'size_n' ] = len( mChunk[ 'data_s' ] )
      mChunk[ 'offset_n' ] = nOffset
      nOffset += mChunk[ 'size_n' ]


    for mChunk in self.chunks_l:
      if mChunk[ 'type_s' ] in [ 'offset', 'size' ]:
        ##  Find chunk whose offset or size must be written.
        nId = mChunk[ 'target_n' ]
        lChunks = [ o for o in self.chunks_l if o[ 'id_n' ] == nId ]
        ##  Id not found or not unique?
        assert 1 == len( lChunks )
        if 'offset' == mChunk[ 'type_s' ]:
          nVal = lChunks[ 0 ][ 'offset_n' ]
        if 'size' == mChunk[ 'type_s' ]:
          nVal = lChunks[ 0 ][ 'size_n' ]
        sData += struct.pack( mChunk[ 'format_s' ], nVal )
      else:
        sData += mChunk[ 'data_s' ]

    return sData


  def clear( self ):
    self.chunks_l = []


  def write( self, s_format, * args ):
    self._write(
      s_format = s_format,
      f_end = False,
      n_id = None,
      args = args )


  def writeEnd( self, s_format, * args ):
    self._write(
      s_format = s_format,
      f_end = True,
      n_id = None,
      args = args )


  def writeArrayEnd( self, s_data, n_id = None ):
    self._write(
      s_format = None,
      f_end = True,
      n_id = n_id,
      args = [ s_data ] )


  def writeOffset( self, s_format, n_offsetId ):
    self.chunks_l.append({
      'type_s': 'offset',
      'format_s': s_format,
      'target_n': n_offsetId,
      'end_f': False,
      'id_n': None,
    })


  def writeSize( self, s_format, n_sizeId ):
    self.chunks_l.append({
      'type_s': 'size',
      'format_s': s_format,
      'target_n': n_sizeId,
      'end_f': False,
      'id_n': None,
    })


  def _write( self, s_format, f_end, n_id, args ):
    ##  Write some integers in specified binary format?
    if s_format:
      self.chunks_l.append({
        'type_s': 'data',
        'data_s': struct.pack( s_format, * args ),
        'end_f': f_end,
        'id_n': n_id,
      })
    ##  Write array?
    else:
      assert 1 == len( args )
      self.chunks_l.append({
        'type_s': 'array',
        'data_s': args[ 0 ],
        'end_f': f_end,
        'id_n': n_id,
      })


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
    ##! Height counts alpha channel mask as a separate image.
    nHeight = nWidth
    ##  Number of color planes.
    assert 1 == oReader.read( '<H' )
    nBpp = oReader.read( '<H' )
    assert nBpp in [ 1, 4, 8, 16, 24, 32 ]
    nCompression = oReader.read( '<I' )
    nImageSize = oReader.read( '<I' )
    ##  Bytes in horizontal line in image.
    nLineSize = ((nWidth * nBpp) / 8) or 1
    ##! Lines are 4-byte aligned.
    nLineSize += nLineSize % 4
    ##  Can be 0 for uncompressed bitmaps.
    if 0 == nImageSize:
      nImageSize = nLineSize * nHeight
    nResolutionCx, nResolutionCy = oReader.read( '<ii' )
    nColorsInPalette = oReader.read( '<I' )
    if 0 == nColorsInPalette and nBpp <= 8:
      nColorsInPalette = pow( 2, nBpp )
    nColorsInPaletteImportant = oReader.read( '<I' )

    sPalette = oReader.readArray( nColorsInPalette * 4 )
    sPixels = oReader.readArray( nImageSize )
    nAlphaSize = 0
    sAlpha = ""

    ##  Since .bmp file don't have notion of transparency, replace some
    ##  colors with violet to mark as transparent. It's not needed for
    ##  |32| bit images since they already have alpha as |4|-th byte in
    ##  each pixel.
    if nBpp < 32:

      nAlphaLineSize = (nWidth / 8) or 1
      ##! Lines are 4-byte aligned.
      nAlphaLineSize += nAlphaLineSize % 4
      nAlphaSize = nAlphaLineSize * nHeight
      sAlpha = oReader.readArray( nAlphaSize )

      ##  In case of 16 colors use violet as transparent color, if
      ##  available.
      for i in range( nColorsInPalette ):
        r, g, b, a = struct.unpack( '!BBBB', sPalette[ i * 4 : i * 4 + 4 ] )
        if 0xFF == r and 0 == g and 0xFF == b:
          nTransparentColorIndex = i
      ##  In case of 256 colors palette use color with index 255 as
      ##  transparent and change it'c palette color to violet.
      if 8 == nBpp:
        sPalette = sPalette[ : -4 ] + struct.pack( '!BBBB', 0xFF, 0, 0xFF, 0 )
        nTransparentColorIndex = 0xFF

      ##  Actual color replacement.
      lPixels = list( sPixels )
      for i in range( nHeight ):
        for j in range( nWidth ):
          nOffset = i * nWidth + j

          nOffsetInBytes = i * nAlphaLineSize + j / 8
          nOffsetInBits = i * nAlphaLineSize * 8 + j
          nByte = ord( sAlpha[ nOffsetInBytes ] )
          if not 0 == (nByte & (1 << (7 - (nOffsetInBits % 8)))):
            ##  For 4 bits per pixel mark transparent with violet color.
            if 4 == nBpp and nTransparentColorIndex is not None:
              nOffsetInBytes = i * nLineSize + (j * nBpp) / 8
              nByte = ord( lPixels[ nOffsetInBytes ] )
              nOffsetInBits = i * nLineSize * 8 + j * nBpp
              ##* Offset inside byte.
              nOffset = nOffsetInBits - nOffsetInBytes * 8
              if 0 == nOffset:
                nByte = (nTransparentColorIndex << 4) | (nByte & 0x0F)
              if 4 == nOffset:
                nByte = (nByte & 0xF0) | nTransparentColorIndex
              lPixels[ nOffsetInBytes ] = chr( nByte )
            ##  For 8 bits per pixel mark transparent with color in
            ##  paleter with index 255:
            if 8 == nBpp:
              nOffsetInBytes = i * nLineSize + (j * nBpp) / 8
              lPixels[ nOffsetInBytes ] = chr( 255 )
            if 24 == nBpp:
              nOffsetInBytes = i * nLineSize + (j * nBpp) / 8
              lPixels[ nOffsetInBytes + 0 ] = chr( 0xFF )
              lPixels[ nOffsetInBytes + 1 ] = chr( 0 )
              lPixels[ nOffsetInBytes + 2 ] = chr( 0xFF )
      sPixels = ''.join( lPixels )

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
      nWidth,
      nHeight,
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
    oIco.images_l.append( oImage )

  return oIco

