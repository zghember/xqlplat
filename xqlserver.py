import select,Queue,socket,thread,threading,sys,time,json
import xqluser

reload(sys)
sys.setdefaultencoding('utf-8')
class MyEncoder(json.JSONEncoder):
    def default(self,obj):
#convert object to a dict
        d = {}
        d.update(obj.__dict__)
        return d

addrmap = {}
namemap = {}
onlineuser = {"msgtype":"onlineuser","data":namemap}
conmap = {}
messagelist = {"msgtype":"message","data":[]}

def msghandler(addr,jsonmsg,s,queues):
    try:
        msg = json.loads(jsonmsg)
    except:
        return
    if msg['msgtype'] == 'loginreq':
        username = msg['username']
        user = xqluser.xqluser(username,addr)
        namemap[username] = user
        conmap[username] = s
        queues[s].put('{"msgtype":"loginres","res":"ok"}')
        print 'loginok',msg,addr
    elif msg['msgtype'] == 'vsbeginreq':
        if msg['from'] in namemap and msg['to'] in namemap and namemap[msg['from']].player2 == 0 and namemap[msg['to']].player2 == 0:
            namemap[msg['from']].player2addr = namemap[msg['to']].udpaddr
            namemap[msg['to']].player2addr = namemap[msg['from']].udpaddr
            namemap[msg['from']].player2 = msg['to']
            namemap[msg['to']].player2 = msg['from']
            queues[s].put('{"msgtype":"vsbeginres","res":"ok","from":"%s","to":"%s"}'%(msg['from'],msg['to']))
            queues[conmap[msg['to']]].put('{"msgtype":"vsbeginres","res":"ok","from":"%s","to":"%s"}'%(msg['from'],msg['to']))
            print 'vs begin',msg
        else:
            queues[s].put('{"msgtype":"vsbeginres","res":"fail"}')
            print 'vs can not begin',msg
    elif msg['msgtype'] == 'vsendreq':
        player2 = namemap[msg['from']].player2
        if player2 and namemap[player2]:
            namemap[player2].player2addr = 0
            namemap[player2].player2 = 0
        namemap[msg['from']].player2addr = 0
        namemap[msg['from']].player2 = 0
    elif msg['msgtype'] == 'refreshvs':
        namemap[msg['from']].alive = time.time()
        namemap[msg['to']].alive = time.time()
    elif msg['msgtype'] == 'msg':
        print "msg",msg
        messagelist['data'].append(msg)

def userhandler():
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.setblocking(False)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR  , 1)
    server_address= ('',9998)
    server.bind(server_address)
    server.listen(100)
#sockets from which we except to read
    inputs = [server]
#sockets from which we expect to write
    outputs = []
    timeout = 2
#Outgoing message queues (socket:Queue)
    message_queues = {}
    prev = 0
    while inputs:
        readable , writable , exceptional = select.select(inputs, outputs, inputs, timeout)
#        if not (readable or writable or exceptional) :
#            print "Time out ! "
        if messagelist["data"]:
            for q in message_queues:
                message_queues[q].put(json.dumps(messagelist))
                if q not in outputs:
                    outputs.append(q)
            messagelist["data"] = []
        if time.time()-prev > 5:
            prev = time.time()
            for q in message_queues:
                message_queues[q].put(MyEncoder().encode(onlineuser))
                if q not in outputs:
                    outputs.append(q)
        #print json.dumps(onlineuser)
#        for user in namemap:
#            if time.time() - namemap[user].alive > 300:
#                namemap[user].player2 = 0
#                namemap[user].player2addr = 0

        for s in readable :
            if s is server:
                connection, client_address = s.accept()
                #print "    connection from ", client_address
                connection.setblocking(0)
                inputs.append(connection)
                message_queues[connection] = Queue.Queue()
            else:
                try:
                    data = s.recv(1024)
                except:
                    data =''
                if data :
                    #print " received " , data , "from ",s.getpeername()
                    msghandler(s.getpeername(),data,s,message_queues)
                    if s not in outputs:
                        outputs.append(s)
                else:
                    print "  closing", client_address
                    if s in outputs :
                        outputs.remove(s)
                    if s in writable:
                        writable.remove(s)
                    for u in conmap:
                        if conmap[u] == s:
                            addr = namemap[u].udpaddr
                            player2 = namemap[u].player2
                            if player2:
                                namemap[player2].player2addr = 0
                                namemap[player2].player2 = 0
                            if addr:
                                addrstr = addr[0] + ':%d'%addr[1]
                                del(addrmap[addrstr])
                            del(namemap[u])
                
                    inputs.remove(s)
                    s.close()
                    #remove message queue 
                    del message_queues[s]
        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except Queue.Empty:
                #print " " , s.getpeername() , 'queue empty'
                outputs.remove(s)
            else:
#               print " sending " , next_msg , " to ", s.getpeername()
                s.send(next_msg)
                     
        for s in exceptional:
            print " exception condition on ", s.getpeername()
            #stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                    outputs.remove(s)
            s.close()
            #Remove message queue
            del message_queues[s]



def fighthandler():
    address = ('', 9999)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(address)

    while True:
        data, addr = s.recvfrom(2048)
        addrstr = addr[0] + ':%d'%addr[1]

#        if not data:
#            print "client %s has exist"%addrstr
            
#        print "received:", data , "from", addrstr

        if 'ping' in data:
            print data
            try:
                msg = json.loads(data)
                namemap[msg['username']].udpaddr = addr
                addrmap[addrstr] = namemap[msg['username']]
            except:
                print "error ping",data
#            s.sendto('"msgtype":"pingok"',addr)
        elif addrmap.has_key(addrstr):
            if addrmap[addrstr].player2 != 0:
                s.sendto(data,addrmap[addrstr].player2addr)
#print "sendingto: ",addrmap[addrstr].player2addr,len(data)
            else:
#            s.sendto('kidding',scmap[jsonmsg['user'][1]])
                print "error not fight"
        else:
#        s.sendto('user not login',addrmap[])
            print "error user not login"

    s.close()


servertcp = threading.Thread(target=userhandler,args=())
servertcp.start()
serverudp = threading.Thread(target=fighthandler,args=())
serverudp.start()
