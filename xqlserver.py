import socket
import json
import xqluser

address = ('42.62.16.233', 9999)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(address)
usermap = {}
onlineuser = []
ipmap = {}

while True:
    data, addr = s.recvfrom(2048)
    addrstr = addr[0] + ':%d'%addr[1]

    if not data:
        print "client %s has exist"%addrstr
        del ipmap[usermap[addrstr].username]
        del usermap[addrstr]
        
#    print "received:", data , "from", addrstr

    if 'login' in data:
        msg = json.loads(data)
        usermap[addrstr] = xqluser.xqluser(msg['username'],addr)
        ipmap[msg['username']] = addrstr
        s.sendto('loginok',addr)
        print 'loginok',msg,addrstr
    elif 'vsbegin' in data:
        msg = json.loads(data)
        if msg['from'] in ipmap and msg['to'] in ipmap:
            usermap[ipmap[msg['from']]].other = usermap[ipmap[msg['to']]].addr
            usermap[ipmap[msg['to']]].other = usermap[ipmap[msg['from']]].addr
            s.sendto('vsbeginok',addr)
            print 'vs begin',msg
        else:
            print 'vs can not begin',msg

    elif usermap.has_key(addrstr):
        if usermap[addrstr].other != 0:
            s.sendto(data,usermap[addrstr].other)
#            print "sendingto: ",usermap[addrstr].other
        else:
#            s.sendto('kidding',scmap[jsonmsg['user'][1]])
            print "error not fight"
    else:
#        s.sendto('user not login',usermap[])
        print "error user not login"

s.close()
