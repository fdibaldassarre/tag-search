#!/usr/bin/env python3

from gi.repository import Gtk

def acceptInterfaceSignals(method):
  def new(self, *args, **kwargs):
    if not self.interface._ignore_signals:
      return method(self, *args, **kwargs)
    else:
      return False
  return new

def ignoreSignals(method):
  def new(self, *args, **kwargs):
    if self._ignore_signals:
      res = method(self, *args, **kwargs)
    else:
      self._ignore_signals = True
      res = method(self, *args, **kwargs)
      self._ignore_signals = False
    return res
  return new


class BasicInterface():
  
  def __init__(self, ts):
    self.ts = ts
    self.db = self.ts.db
    # Signals control: set to True when modifying the interface
    #                  to avoid sending signals when editing widgets.
    #                  Use decorator @ignoreSignals in an interface method and the
    #                  @acceptInterfaceSignal in the signal handler methods which you want to accidentally trigger
    self._ignore_signals = False
    # Logger
    self.log = self.ts.log
  
  def showInfoWindow(self, title, message=None):
    self._showWindow(title, window_type=Gtk.MessageType.INFO, message=message)
  
  def showErrorWindow(self, title, message=None):
    self._showWindow(title, window_type=Gtk.MessageType.ERROR, message=message)
    
  def _showWindow(self, title, window_type, message=None):
    dialog = Gtk.MessageDialog(self.main_window, 0, window_type, Gtk.ButtonsType.OK, title)
    if message is not None:
      dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()
