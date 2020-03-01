# coding = utf-8
# using namespace std
from lib.auth.authcore import SocketConfig

sk = SocketConfig("lib/auth/config.json")
print("ok")
sk.config['Name'] = "teste"
with open(sk.file_got, "r") as dt: ss = sk.AddrConfig(dt.read())
try: print(ss)
except Exception: pass
del sk

