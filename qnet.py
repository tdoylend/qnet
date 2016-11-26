# QNet Library
# (C) 2016 Thomas Doylend
#
# This software is released under the terms of the MIT License.
#
#
# INTERNET IN GENERAL:
#
# Communications over the internet take place between two computers. One pro-
# vides the service (such as a printer, cloud storage, etc). This computer is
# called the 'server'. The other side is the client. A client communicates
# with the server to use the service offered.
#
# One server may have many clients, and a computer can act as a client to many
# servers at the same time.
#
# Servers on the Internet are identified by their IP address. Similar to a
# phone number, an IP address identifies computers. Many servers are also
# identified by a domain name - also called a web address - such as google.com
#
# When you type 'google.com' into your web browser, a service called DNS
# translates that web address into the IP address of the nearest Google
# server. Then your computer - the client - can request the services of the
# Google server: its search engine.
#
# A server has many ports, and each port can provide a different service. For
# example, the GMail server provides a friendly-looking interface on port 80
# (the port for web browsers.) It uses another port to accept connections from
# other email servers delivering mail sent to GMail accounts.
#
# Most low-numbered ports are already assigned specific functions. For
# example, port 80 is ALWAYS the port used for web browsers to connect. If you
# wish to write your own server, make sure to use a high-numbered port (ports
# higher than 4096 usually work well.)
#
# Note that port numbers do not go above 65535 (2^16 - 1).
#
#
# QNET PROTOCOL:
#
# QNet is a very simple way for a server and a client to talk to one another.
# In QNet, communications between the server and the client look like this:
#
#       1) The client sends a string to the server.
#       2) The server responds with another string.
#       3) The conversation is finished.
#
# In order to send more data, the client has to open another conversation.
#
# All QNet servers are expected to support the following requests:
#
#       is_q:       Respond with 'yes', indicating that this is a QNet server.
#       who:        Respond with the server name.
#       motd:       Respond with the Message Of The Day (MOTD).
#
#
# QNET LIBRARY:
#
# The Connection class creates a connection to a server. You can perform as
# many conversations as you want on the same connection.
#
# The converse() function handles a conversation. It takes one parameter: the
# message you want to send. It returns the server's response.
#
# The QNetServer class creates a QNet server. In order to use it, you simply
# subclass it and override the default functions. See the example programs for
# ways to do this.
#
#
# GENERAL NOTES:
#
# Never, ever, EVER send passwords over the network. It is fairly
# easy to watch someone's network traffic and extract all sorts of data.
# Boil your password down using an irreversable algorithm like MD5. For more
# information on doing this, look at Python's built-in hashlib library.
#
# Enjoy!

SIZE_RANGE  = 1000000
SIZE_DIGITS = 6

import socket
import time

try:
    import cryptography
except ImportError:
    cryptography = None

class Connection:
    def __init__(self,address,port):
        #Initialize the connection. A connection is composed of multiple
        #conversations.
        #
        #The arguments are the web or IP address and the port number.
        #
        #Example:
        #
        # >>> c = Connection('192.168.1.128',4099)
    
        self.address = address
        self.port = port

    def converse(self,msg):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Create a socket
        s.connect((self.address,self.port)) #Connect to the server

        any_send(s,msg)

        result = any_receive(s)

        s.close()

        return result

def get_address():
    #This function will attempt to determine what address you should serve
    #as.

    return socket.gethostname()

class QNetServer:
    def __init__(self,address,port,auto_strip=False,queue_size=5):
        #Server. The arguments are the address and port to serve as.
        #
        #Use the IP address of your own computer (you can usually find it in
        #the Network Settings, or Linux users can type 'hostname -I' in their
        #terminal.)
        #
        #The auto_strip parameter tells the server whether or not to remove
        #whitespace (newlines, spaces, and tabs) from the beginning and end
        #of each incoming message. By default, this feature is turned off.
        #
        #The queue_size parameter tells the server how many connections you
        #can place in a 'waiting line' before new connections are denied. The
        #default is five.
        #
        #This server is NOT multi-threaded: it only uses one processor on your
        #machine. If you have a quad-core machine, you can run FOUR servers
        #about as fast as you can run ONE.

        self.address = address
        self.port = port
        self.shutdown_pending = False
        self.auto_strip = auto_strip
        self.queue_size = queue_size

        self.setup()

    def setup(self):
        #Place any initialization here.
        return

    def who(self):
        #Return the 'who' message for the server.
        return 'Test QNet Server'
    
    def motd(self):
        #Return the MOTD for the server.
        return 'This is the MOTD.'

    def bad(self,packet,client_address,client_port):
        #This method is called whenever the server receives a malformed
        #packet (i.e. one that has been mangled in transit). It will collect
        #as much data as it can and pass it to you.
        #It is your decision whether to attempt to recover this data or to
        #throw it out.
        #
        #By default, an message will be printed to the console.
        #
        #Note that the server does NOT attempt to respond to malformed
        #packets, and returning a value from this function has no effect.

        print 'Received bad packet from',client_address
    
    def handle(self,packet,client_address,client_port):
        #This function is similar to using converse(), but exactly in reverse.
        #You are passed the data that was sent, and you return your
        #response.
        #
        #One way to think of it is as if you were defining the converse()
        #function itself.
        #
        #By default, this function prints the received packet and returns 'OK',
        #and shuts down if the comman 'shutdown' is received.

        print 'Received:',packet

        if packet == 'shutdown':
            self.set_shutdown_pending()
            print 'Shutting down soon...'

        return 'OK'
    
    def set_shutdown_pending(self):
        #Calling this function tells the server that you wish to shut down.
        #The server will finish any tasks and gracefully turn off.
        self.shutdown_pending = True
    
    def serve(self):
        #Calling this function starts the server. 
        #
        #This function returns some time after you have set the shutdown
        #flag using set_shutdown_pending().
        #
        #Crashing the server will have disastrous results, usually requiring
        #that you restart your computer. Please avoid this.
        #
        #NOTE: It seems that Linux locks the port after the server shuts down,
        #making it impossible to open a new server on the same port.
        #This appears to be a bug, and no workaround has yet been found.
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_socket.bind((self.address,self.port))

        server_socket.listen(self.queue_size)

        while not self.shutdown_pending:
            (client_socket,(client_address,client_port)) = server_socket.accept()

            try:
                data = any_receive(client_socket)
                if data == 'who':
                    response = self.who()
                elif data == 'motd':
                    response = self.motd()
                else:    
                    response = self.handle(data,client_address,client_port)
                
                respond = True
            except:
                respond = False
                self.bad(client_socket.recv(4096),client_address,client_port)

            if respond:
                try:
                    any_send(client_socket,response)
                except:
                    print 'ERROR in Sending'
            client_socket.close()

        
        server_socket.shutdown(socket.SHUT_RDWR)
        server_socket.close()

def any_receive(s):
    recv_info = s.recv(SIZE_DIGITS)
    if (len(recv_info) != SIZE_DIGITS) or (not recv_info.isdigit()):
        raise RuntimeError("The connection was broken in some way - we got a malformed info header.")
    
    recv_size = int(recv_info)

    received_bytes = 0
    received_data = ''

    while received_bytes < recv_size:
        received_just_now = s.recv(4096)
        if len(received_just_now) == 0:
            raise RuntimeError("The connection was broken in some way - we've stopped receiving data.")
        
        received_bytes += len(received_just_now)
        received_data  += received_just_now
    
    return received_data

def any_send(s,msg):
    if len(msg) >= SIZE_RANGE:
        raise ValueError('Message is too long: limit is '+str(SIZE_RANGE-1)+' characters.')
    
    size_info = str(len(msg)).rjust(SIZE_DIGITS,'0')

    msg = size_info+msg
    sent_bytes = 0
    while sent_bytes < len(msg):
        sent_just_now = s.send(msg[sent_bytes:])
        if sent_just_now == 0:
            raise RuntimeError("The connection was broken in some way - we've stopped sending data.")
        sent_bytes += sent_just_now

#If this program is run (instead of being imported)
#it will create a demo server.
if __name__ == '__main__':
    server = QNetServer('localhost',4099)
    print 'Serving...'
    server.serve()