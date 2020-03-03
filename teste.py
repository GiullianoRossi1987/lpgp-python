# coding = utf-8
# using namespace std
from config.configurations import Configurations

con = Configurations("config/gen.json")
con.commit()
del con
print("ok")



