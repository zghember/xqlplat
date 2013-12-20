
import socket
import time,string
import ConfigParser

config = ConfigParser.ConfigParser()
config.read("config.ini")

#user = raw_input("username:")
#to = raw_input("playername:")
user = config.get("USER","USERNAME")
server = ('%s'%config.get("SERVER","IP"), string.atoi(config.get("SERVER","PORT")))
local = ('', string.atoi(config.get("USER","PORT")))
xql = ('localhost', string.atoi(config.get("USER","XQLPORT")))
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(local)


loginok = 0
print 'connecting to server...'
while not loginok:
	s.sendto('{"type":"login","username":"%s"}'%(user),server)
	time.sleep(5)
	data, addr = s.recvfrom(2048)
	if 'loginok' in data:
		loginok = 1
print 'login success'


while True:
	beginstatus = 0
	clienttype = 10
	while (clienttype !='0' and clienttype != '1'):
		clienttype = raw_input("server(0) or client(1):")
	if clienttype == '0':
		print "waiting for fight..."
		beginstatus = 1	
	else:
		to = raw_input("player2's name:")
		print "trying to begin fight with %s"%to
		times = 0
		while not beginstatus:
			s.sendto('{"type":"vsbegin","from":"%s","to":"%s"}'%(user,to),server)
			time.sleep(5)
			data, addr = s.recvfrom(2048)
			if 'vsbeginok' in data:
				beginstatus = 1
			times = times + 1
			if times == 5:
				break
	if beginstatus == 0:
		print "can not begin fight with %s"%to
	while beginstatus:
		data, addr = s.recvfrom(2048)
		if '127.0' in addr[0]:
			s.sendto(data,server)
		else:
			s.sendto(data, xql)
#		print data ,"from",addr

s.close()
