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

    oBmp = bmp.Bmp()
    oBmp.fromBmp( arg.data_s )
    ##  User can assign new bitmap, so reload image parameters from it.
    arg.width_n = oBmp.width()
    arg.height_n = oBmp.height()
    arg.colors_n = oBmp.colors()
    arg.planes_n = 1
    arg.bpp_n = oBmp.bpp()
    arg.data_s = oBmp.toIco()

    nWidth = arg.width_n
    assert nWidth <= 256
    if 256 == nWidth:
      nWidth = 0
    self.writer_o.write( '<B', nWidth )

    nHeight = arg.width_n
    assert nHeight <= 256
    if 256 == nHeight:
      nHeight = 0
    ##! Bitmaps in ICO contains 'AND mask', it's data is written after
    ##  pixel data. To indicate presence of this mask, image height is
    ##  doubled.
    ##! 32-bit images may skip 'AND mask', but it's a good pactice to keep
    ##  it for optimization reasons, bacward compatibility and tolerance to
    ##  programs that can't handle it's absence.
    self.writer_o.write( '<B', arg.height_n * 2 )
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

