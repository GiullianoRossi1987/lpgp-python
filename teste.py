# coding = utf-8
# using namespace std
from lib.core import MySQLConnectionOptions
from lib.core import MySQLExternalConnection
from lib.auth.authcore import Client4
from lib.client_data import ClientDataAuto

client = Client4("lib/auth/config.json")
response, access_nm, access_pas = client.connect_auth(True)

mo = MySQLConnectionOptions("lib/mysql-config.json")
cl = ClientDataAuto(mo.document['General']['Primary-Host'], access_nm, "")

cl.fetch_auth()

mysqlInstance = MySQLExternalConnection(mo, access_nm)
