#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

# pyico binary reader and writer.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

import struct


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
      assert 1 == len( args ) and args[ 0 ]
      self.chunks_l.append({
        'type_s': 'array',
        'data_s': args[ 0 ],
        'end_f': f_end,
        'id_n': n_id,
      })

