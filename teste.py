# coding = utf-8
# using namespace std
from lib.core import MySQLConnectionOptions
from lib.core import MySQLExternalConnection
from lib.auth.authcore import Client4

client = Client4("lib/auth/config.json")
response, access_nm, access_pas = client.connect_auth(True)

mo = MySQLConnectionOptions("lib/mysql-config.json")

ext = MySQLExternalConnection(mo, access_nm)
print("ok")