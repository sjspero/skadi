from __future__ import absolute_import

import collections as c
import io
import itertools

from skadi.io import protobuf as pb_io
from skadi.state.demo import *

class Demo(object):
  def __init__(self):
    self._file_header = None
    self._server_info = None
    self._voice_init = None
    self._game_event_list = None
    self._set_view = None
    self._class_info = None
    self._string_tables = None
    self._send_tables = None
    self._recv_tables = None

  def __repr__(self):
    lenst = len(self._send_tables)
    lenrt = len(self._recv_tables)
    return '<Demo ({0} send, {1} recv)>'.format(lenst, lenrt)

  @property
  def file_header(self):
    return self._file_header

  @file_header.setter
  def file_header(self, pbmsg):
    file_header = {}
    to_extract = (
      'demo_file_stamp', 'network_protocol', 'server_name', 'client_name',
      'map_name', 'game_directory', 'fullpackets_version'
    )
    for attr in to_extract:
      file_header[attr] = getattr(pbmsg, attr)
    self._file_header = file_header

  @property
  def server_info(self):
    return self._server_info

  @server_info.setter
  def server_info(self, pbmsg):
    to_extract = (
      'protocol', 'server_count', 'is_dedicated', 'is_hltv',
      'c_os', 'map_crc', 'client_crc', 'string_table_crc',
      'max_clients', 'max_classes', 'player_slot',
      'tick_interval', 'game_dir', 'map_name', 'sky_name',
      'host_name'
    )
    self._server_info = {(v,getattr(pbmsg,v)) for v in to_extract}

  @property
  def voice_init(self):
    return self._voice_init

  @voice_init.setter
  def voice_init(self, pbmsg):
    to_extract = ('quality', 'codec')
    self._voice_init = {(v,getattr(pbmsg,v)) for v in to_extract}

  @property
  def game_event_list(self):
    return self._game_event_list

  @game_event_list.setter
  def game_event_list(self, pbmsg):
    game_event_list = {}
    for desc in pbmsg.descriptors:
      _id, name = desc.eventid, desc.name
      keys = [(k.type, k.name) for k in desc.keys]
      game_event_list[_id] = GameEvent(_id, name, keys)
    self._game_event_list = game_event_list

  @property
  def send_tables(self):
    return self._send_tables

  @send_tables.setter
  def send_tables(self, pbmsg):
    packet_io = pb_io.PacketIO.wrapping(pbmsg.data)
    send_tables = {}
    for svc_message in iter(packet_io):
      st = SendTable.construct(svc_message)
      send_tables[st.dt] = st
    self._send_tables = send_tables

  @property
  def recv_tables(self):
    return self._recv_tables

  @property
  def class_info(self):
    return self._class_info

  @class_info.setter
  def class_info(self, pbmsg):
    class_info = {}
    for c in pbmsg.classes:
      _id, dt, name = c.class_id, c.table_name, c.network_name
      class_info[c.class_id] = Class(_id, name, dt)
    self._class_info = class_info

  @property
  def string_tables(self):
    return self._string_tables

  @string_tables.setter
  def string_tables(self, pbmsg):
    string_tables = {}
    for t in pbmsg.tables:
      _ii, _iic = [], []
      for i in t.items:
        _ii.append(String(i.str, i.data))
      for i in t.items_clientside:
        _iic.append(String(i.str, i.data))
      name, flags = t.table_name, t.table_flags
      string_tables[name] = StringTable(name, flags, _ii, _iic)
    self._string_tables = string_tables

  def flatten_send_tables(self):
    test_needs_decoder = lambda st: st.needs_decoder
    recv_tables = {}
    for st in filter(test_needs_decoder, self.send_tables.values()):
      recv_tables[st.dt] = Flattener(self).flatten(st)
    self._recv_tables = recv_tables