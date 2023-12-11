'''Classes for virtual LocalTalk networks.'''

from collections import deque
from threading import Lock

from . import LocalTalkPort
from ...netlog import log_localtalk_frame_inbound, log_localtalk_frame_outbound


class VirtualLocalTalkPort(LocalTalkPort):
  '''Virtual LocalTalk Port.'''
  
  def __init__(self, virtual_network, short_str=None, network=0):
    super().__init__(network=network, respond_to_enq=True)
    self._virtual_network = virtual_network
    self._short_str = short_str or 'Virtual'
  
  def short_str(self): return self._short_str
  __str__ = short_str
  __repr__ = short_str
  
  def _recv_packet(self, packet_data):
    log_localtalk_frame_inbound(packet_data, self)
    self.inbound_packet(packet_data)
  
  def start(self, router):
    self._virtual_network.plug(self._recv_packet)
    super().start(router)
  
  def stop(self):
    super().stop()
    self._virtual_network.unplug(self._recv_packet)
  
  def send_packet(self, packet_data):
    log_localtalk_frame_outbound(packet_data, self)
    self._virtual_network.send_packet(packet_data, self._recv_packet)


class VirtualLocalTalkNetwork:
  '''Virtual LocalTalk network.'''
  
  def __init__(self):
    self._plugged = deque()
    self._lock = Lock()
  
  def plug(self, recv_func):
    with self._lock: self._plugged.append(recv_func)
  
  def unplug(self, recv_func):
    with self._lock: self._plugged.remove(recv_func)
  
  def send_packet(self, packet_data, recv_func):
    function_calls = deque()
    with self._lock:
      for func in self._plugged:
        if func == recv_func: continue
        function_calls.append((func, packet_data))
    for func, packet_data in function_calls: func(packet_data)