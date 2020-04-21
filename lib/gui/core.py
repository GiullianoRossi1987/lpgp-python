# coding = utf-8
# using namespace std
from tkinter import *
from sys import exit as die  # PHP here :)
from config.configurations import Configurations
from lib.logger import DefaultLogger

gbl_config = Configurations("config/gen.json")
rd_gui = gbl_config.document['GUI']

gui_logs = DefaultLogger("logs/gui.log")


class ErrorDialog(object):
	"""
	That method is a global dialog box adapted to the system errors. It's used to show any trouble the system would have.
	It will work at every exception raised at the system runtime.

	:cvar message: The error message used.
	:cvar error_code: The error code received
	:cvar mainFrame: The main frame object used
	:cvar window: The TK object.
	"""

	message: str
	error_code: int
	window: Tk = Tk()
	mainFrame: Frame = Frame(window)

	def __init__(self, message: str, error_code: int = 982):
		"""
		Starts the class and launch the dialog message and exit the application execution.
		:param message: The error message.
		:param error_code: The error code, if the exception don't have a error code, then it will be 982
		"""
		err_lb = Label(self.mainFrame)
		err_lb['text'] = f"Fatal error [{error_code}]: {message}"
		btn_dimiss = Button(master=self.mainFrame)
		btn_dimiss['command'] = lambda: die()
		btn_dimiss['text'] = "Ok"
		btn_dimiss['width'] = 5
		self.message = message
		self.error_code = error_code
		err_lb.pack()
		btn_dimiss.pack()
		self.mainFrame.pack()
		self.window.mainloop()

