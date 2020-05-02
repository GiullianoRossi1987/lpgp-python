# coding = utf-8
# using namespace std
from .lib.auth.authcore import SocketConfig, Client4
from .lib.core import *
from .lib.logger import DefaultLogger as Logger
from .lib.logger import Envvars
from .config.configurations import Configurations as Conf
from typing import AnyStr


def authClient(clientAuth: AnyStr, sconfig: AnyStr) -> tuple:
	"""
	That function authenticate the client file
	:param clientAuth: The client authentication file
	:param sconfig: The socket configuration file
	:return: The authentication results
	"""
	client = Client4(sconfig)
	return client.ext_connect_auth(clientAuth, False)


def authCInternal(sconfig: AnyStr) -> tuple:
	"""
	That function authenticate the internal client file, requiring only the socket configurations file
	:param sconfig: The socket configurations file.
	:return: The authentication results;
	"""
	client = Client4(sconfig)
	return client.connect_auth(False)


def authCPure(socketConfig: SocketConfig) -> tuple:
	"""
	That function authenticate a internal client file but using a socket configurations object to
	:param socketConfig: The socket configurations object.
	:return: The authentication results;
	"""
	client = Client4(socketConfig.file_got)
	return client.connect_auth(False)


def startDB(usr_access: str, pass_access: str, mconfig: AnyStr) -> MySQLExternalConnection:
	"""
	That method starts a database using the default options
	:param usr_access: The user to access the database
	:param pass_access: The user password
	:param mconfig: The mysql default configurations file
	:return: The connection object started
	"""
	config = MySQLConnectionOptions(mconfig)
	return MySQLExternalConnection(config, usr_access, pass_access)


def authAll(clientF: AnyStr, signature: AnyStr, sconfig: AnyStr, mconfig: AnyStr, talkback: AnyStr) -> bool:
	"""
	That method does everything at the authentication, it's normally used by the developers which doesn't need a complete
	application, they just will use it for authenticate the client data and the signature data in their product.
	:param clientF: The client file to authenticate
	:param signature: The main signature file to authenticate
	:param sconfig: The socket configurations file using
	:param mconfig: The mysql configurations file
	:return: True if all was successful
	"""
	client = Client4(sconfig)
	dt = client.ext_connect_auth(clientF, True, talkback)
	config = MySQLConnectionOptions(mconfig)
	db = MySQLSignaturesManager(config, str(dt[1]), str(dt[2]))
	db.authenticate_file(signature)
	return True
