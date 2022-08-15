# code from:
# https://www.reddit.com/r/learnpython/comments/3psujz/efficiently_waiting_for_multiple_event_objects/
# TODO: adapt to use oclock.Event() instead..

import threading



class big_event(threading.Event):
  def __init__(self, e=None):
    super().__init__()
    self.extra_event=e

  def set(self):
    super().set()
    if self.extra_event:
      self.extra_event.set()


