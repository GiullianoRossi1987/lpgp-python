# coding = utf-8
# using namespace std
from lib.auth.authcore import SocketConfig, Client4

sock = Client4("lib/auth/config.json")
a = sock.connect_auth(False)
print(a)


