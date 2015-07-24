import socket
import threading
import random
import string
from time import sleep

class coordinate(object):

    def __init__(self, ctlip, ctlport_remote, ctlport_local, localcert, remotecert, localpub, required):
        self.count = 0
        self.available = 0
        self.remotepub = remotecert
        self.localcert = localcert
        self.authdata = localpub
        self.required = required
        
        self.recvs = []
        #TODO: make the following string more random
        salt = list(string.ascii_letters)
        random.shuffle(salt)
        self.str = ''.join(salt[:16])
        self.udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpsock.bind(('', ctlport_local))
        self.addr = (ctlip, ctlport_remote)
        self.check = threading.Event()
        self.check.set()
        req = threading.Thread(target=self.reqconn)
        req.start()

    def newconn(self, recv):
        self.available += 1
        self.count += 1
        self.recvs.append(recv)
        if self.issufficient():
            self.check.clear()
        print("Available socket %d" % self.available)
            
    def closeconn(self):
        self.count -=1
        self.available -= 1
        if not self.issufficient():
            self.check.set()
        print("Available socket %d" % self.available)

    def reqconn(self):
        while True:
            self.check.wait()
            requestdata = self.generatereq()      
            self.udpsock.sendto(requestdata, self.addr)
            if self.available + 2 >= self.required:
                sleep(0.1) 
            else:
                sleep(0.05)
            
    def generatereq(self):
        salt = list(string.ascii_letters)
        random.shuffle(salt)
        salt = salt[:16]
        saltstr = ''.join(salt)
        return  (bytes(saltstr, "UTF-8")
                +bytes(self.authdata, "UTF-8")
                +bytes('%X' % self.localcert.sign(bytes(saltstr,"UTF-8"), None)[0], "UTF-8")
                +self.remotepub.encrypt(bytes(self.str, "UTF-8"), None)[0]) #TODO: Replay attack?

    def issufficient(self):
        return self.available >= self.required
    
    def offerconn(self):
        if self.available <=0:
            return None
        self.available -=1
        offer = self.recvs [0]
        self.recvs = self.recvs[1:]
        if not self.issufficient():
            self.check.set()
        print("Available socket %d" % self.available)
        return offer
