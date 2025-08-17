import socket

class SystemInfoManager:
  def get_default_address(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      s.connect(("8.8.8.8", 80))
      return s.getsockname()[0]
    finally:
      s.close()
