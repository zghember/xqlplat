import select,Queue,socket,thread,threading,sys
import json
import xqluser

reload(sys)
sys.setdefaultencoding('utf-8')

usermap = {}
onlineuser = []
ipmap = {}
conmap = {}

def msghandler(addr,jsonmsg,s,queues):
    msg = json.loads(jsonmsg)
    addrstr = addr[0] + ':%d'%addr[1]
    if msg['msgtype'] == 'loginreq':
        usermap[addrstr] = xqluser.xqluser(msg['username'],addr)
        ipmap[msg['username']] = addrstr
        conmap[msg['username']] = s	
        queues[s].put('{"msgtype":"loginres","res":"ok"}')
        print 'loginok',msg,addrstr
    elif msg['msgtype'] == 'vsbeginreq':
        if msg['from'] in ipmap and msg['to'] in ipmap:
            usermap[ipmap[msg['from']]].other = usermap[ipmap[msg['to']]].addr
            usermap[ipmap[msg['to']]].other = usermap[ipmap[msg['from']]].addr
            queues[s].put('{"msgtype":"vsbeginres","res":"ok","from":"%s","to":"%s"}'%(msg['from'],msg['to']))
            queues[conmap[msg['to']]].put('{"msgtype":"vsbeginres","res":"ok","from":"%s","to":"%s"}'%(msg['from'],msg['to']))
            print 'vs begin',msg
        else:
            queues[s].put('{"vsbeginres":"fail"}')
            print 'vs can not begin',msg

       
    

def userhandler():
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.setblocking(False)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR  , 1)
    server_address= ('',9998)
    server.bind(server_address)
    server.listen(10)
#sockets from which we except to read
    inputs = [server]
#sockets from which we expect to write
    outputs = []
#Outgoing message queues (socket:Queue)
    message_queues = {}
     
    while inputs:
        readable , writable , exceptional = select.select(inputs, outputs, inputs)
        for s in readable :
            if s is server:
                connection, client_address = s.accept()
                print "    connection from ", client_address
                connection.setblocking(0)
                inputs.append(connection)
                message_queues[connection] = Queue.Queue()
            else:
                data = s.recv(1024)
                if data :
                    print " received " , data , "from ",s.getpeername()
                    msghandler(s.getpeername(),data,s,message_queues)
                    if s not in outputs:
                        outputs.append(s)
                else:
                    print "  closing", client_address
                    if s in outputs :
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    #remove message queue 
                    del message_queues[s]
        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except Queue.Empty:
                print " " , s.getpeername() , 'queue empty'
                outputs.remove(s)
            else:
                print " sending " , next_msg , " to ", s.getpeername()
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

        if not data:
            print "client %s has exist"%addrstr
            
#    print "received:", data , "from", addrstr

        if usermap.has_key(addrstr):
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


servertcp = threading.Thread(target=userhandler,args=())
servertcp.start()
serverudp = threading.Thread(target=fighthandler,args=())
serverudp.start()
