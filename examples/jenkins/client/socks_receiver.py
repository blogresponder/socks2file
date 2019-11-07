#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import sys
import time

from filesocket import filesocket

'''path to temporary directory used for file sockets'''
SOCKSER_DIR =''


'''SOCKS5 RFC described connection methods'''
CONNECT = 1
BIND = 2
UDP_ASSOCIATE = 3

'''SOCKS5 RFC described supported address types'''
IPV4 = 1
DOMAINNAME = 3
IPV6 = 4

'''ERROR messages'''
CONNECT_SUCCESS = 0
ERROR_ATYPE = "[-] Client address error!"
ERROR_VERSION = "[-] Client version error!"
ERROR_METHOD = "[-] Client method error!"
ERROR_RSV = "[-] Client Reserved byte error!"
ERROR_CMD = "[-] Command not implemented by server error!"

''' Reserver byte '''
RSV = 0
''' '''
BNDADDR = "\x00" * 4
BNDPORT = "\x00" * 2

'''SOCKS VERSION (used in initial negotiation)'''
SOCKS_VERSION = 5

# ALLOWED_METHOD = [0, 2]
ALLOWED_METHOD = [0]

def main():
    global SOCKSER_DIR
    if len(sys.argv) != 4:
        print "Usage : "
        print "\tpython %s [L_HOST] [L_PORT] [SOCKSER_TMP_DIRECTORY]" % (sys.argv[0])
        print "Example : "
        print "\tpython %s 127.0.0.1 1080 /tmp/sockser/" % (sys.argv[0])
        exit(1)

    LOCAL_HOST = sys.argv[1]
    LOCAL_PORT = int(sys.argv[2])
    MAX_CONNECTION = 0x100
    SOCKSER_DIR = sys.argv[3]
    
    if SOCKSER_DIR[-1] != '/':
        SOCKSER_DIR += '/'
    print "Sockser dir :" + SOCKSER_DIR

    server(LOCAL_HOST, LOCAL_PORT, MAX_CONNECTION)


def server(local_host, local_port, max_connection):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((local_host, local_port))
        server_socket.listen(max_connection)
        print '[+] Server started [%s:%d]' % (local_host, local_port)
        while True:
            local_socket, local_address = server_socket.accept()
            print '[+] Detect connection from [%s:%s]' % (local_address[0], local_address[1])
            result = socks_selection(local_socket)
            if not result[0]:
                print "[-] socks selection error!"
                break
            result = socks_request(result[1])
            if not result[0]:
                print "[-] socks request error!"
                break
            local_socket, remote_socket = result[1]
            # TODO : loop all socket to close...
        print "[+] Releasing resources..."
        local_socket.close()
        print "[+] Closing server..."
        server_socket.close()
        print "[+] Server shuted down!"
    except  KeyboardInterrupt:
        print ' Ctl-C stop server'
        try:
            remote_socket.close()
        except:
            pass
        try:
            local_socket.close()
        except:
            pass
        try:
            server_socket.close()
        except:
            pass
        return


def socks_selection(socket):
    '''Parses first request and retrieves client info (host,port,socks version and method)'''

    ''' retrieves client supported version number'''
    client_version = ord(socket.recv(1))
    print "[+] client version : %d" % client_version

    ''' checks if client supported version is supported by server'''
    if not client_version == SOCKS_VERSION:
        socket.shutdown(socket.SHUT_RDWR)
        socket.close()
        return False, ERROR_VERSION

    ''' retrieves client supported connection methods'''
    support_method_number = ord(socket.recv(1))

    print "[+] Client Supported method number : %d" % support_method_number

    ''' creates supported methods list'''
    support_methods = []
    for i in range(support_method_number):
        method = ord(socket.recv(1))
        print "[+] Client Method : %d" % method
        support_methods.append(method)

    ''' chooses method from those supported'''
    selected_method = None
    for method in ALLOWED_METHOD:
        if method in support_methods:
            selected_method = 0

    ''' checks if method was chosen '''
    if selected_method is None:
        socket.shutdown(socket.SHUT_RDWR)
        socket.close()
        return False, ERROR_METHOD

    ''' sends chosen method to client '''
    print "[+] Server select method : %d" % selected_method
    response = chr(SOCKS_VERSION) + chr(selected_method)
    socket.send(response)

    ''' returns socket if everything went well'''
    return True, socket


def socks_request(local_socket):

    # start SOCKS negotiation
    client_version = ord(local_socket.recv(1))
    print "[+] client version : %d" % client_version
    if not client_version == SOCKS_VERSION:
        local_socket.shutdown(socket.SHUT_RDWR)
        local_socket.close()
        return False, ERROR_VERSION
    cmd = ord(local_socket.recv(1))
    if cmd == CONNECT:
        print "[+] CONNECT request from client"
        rsv  = ord(local_socket.recv(1))
        if rsv != 0:
            local_socket.shutdown(socket.SHUT_RDWR)
            local_socket.close()
            return False, ERROR_RSV
        atype = ord(local_socket.recv(1))

        if atype == IPV4:
            dst_address = ("".join(["%d." % (ord(i)) for i in local_socket.recv(4)]))[0:-1]

            print "[+] IPv4 : %s" % dst_address
            dst_port = ord(local_socket.recv(1)) * 0x100 + ord(local_socket.recv(1))
            print "[+] Port : %s" % dst_port

            ''' setting up filesocket '''
            remote_socket = filesocket.filesocket(socket_dir = SOCKSER_DIR)

            try:
                print "[+] Fake connecting : %s:%s" % (dst_address, dst_port)
                timestamp = str(int(time.time()))
                remote_socket.connect((dst_address, dst_port),timestamp)

                response = ""
                response += chr(SOCKS_VERSION)
                response += chr(CONNECT_SUCCESS)
                response += chr(RSV)
                response += chr(IPV4)
                response += BNDADDR
                response += BNDPORT
                local_socket.send(response)
                print "[+] Tunnel connected! Transferring data..."
                r = threading.Thread(target=transfer_in, args=(
                    local_socket, remote_socket))
                r.start()
                s = threading.Thread(target=transfer_out, args=(
                    remote_socket, local_socket))
                s.start()
                return True, (local_socket, remote_socket)
            except socket.error as e:
                print e
                remote_socket.shutdown(socket.SHUT_RDWR)
                remote_socket.close()
                local_socket.shutdown(socket.SHUT_RDWR)
                local_socket.close()
        elif atype == DOMAINNAME:
            domainname_length = ord(local_socket.recv(1))
            domainname = ""
            for i in range(domainname_length):
                domainname += (local_socket.recv(1))

            print "[+] Domain name : %s" % (domainname)
            dst_port = ord(local_socket.recv(1)) * 0x100 + ord(local_socket.recv(1))
            print "[+] Port : %s" % (dst_port)

            # SETTING UP FILENAME instead of preparing socket
            remote_socket = filesocket.filesocket(socket_dir = SOCKSER_DIR)

            try:
                print "[+] Fake connecting : %s:%s" % (domainname, dst_port)
                timestamp = str(int(time.time()))
                remote_socket.connect((domainname, dst_port),timestamp)

                response = ""
                response += chr(SOCKS_VERSION)
                response += chr(CONNECT_SUCCESS)
                response += chr(RSV)
                response += chr(IPV4)
                response += BNDADDR
                response += BNDPORT
                local_socket.send(response)
                print "[+] Tunnel connected! Transferring data..."
                r = threading.Thread(target=transfer_in, args=(
                    local_socket, remote_socket))
                r.start()
                s = threading.Thread(target=transfer_out, args=(
                    remote_socket, local_socket))
                s.start()
                return (True, (local_socket, remote_socket))
            except socket.error as e:
                print e
                remote_socket.shutdown(socket.SHUT_RDWR)
                remote_socket.close()
                local_socket.shutdown(socket.SHUT_RDWR)
                local_socket.close()
        elif atype == IPV6:
            #TODO
            dst_address = int(local_socket.recv(4).encode("hex"), 16)
            print "[+] IPv6 : %x" % (dst_address)
            dst_port = ord(local_socket.recv(1)) * 0x100 + ord(local_socket.recv(1))
            print "[+] Port : %s" % (dst_port)

            # TODO IPv6 under constrution
            print "IPv6 support under constrution"
            local_socket.shutdown(socket.SHUT_RDWR)
            local_socket.close()
            return (False, ERROR_ATYPE)
        else:
            local_socket.shutdown(socket.SHUT_RDWR)
            local_socket.close()
            return (False, ERROR_ATYPE)
    elif cmd == BIND:
        # TODO
        print "socks5 BIND command is not supported for now."
        local_socket.shutdown(socket.SHUT_RDWR)
        local_socket.close()
        return (False, ERROR_CMD)
    elif cmd == UDP_ASSOCIATE:
        # TODO
        print "socks5 UDP_ASSOCIATE command is not supported for now."
        local_socket.shutdown(socket.SHUT_RDWR)
        local_socket.close()
        return (False, ERROR_CMD)
    else:
        local_socket.shutdown(socket.SHUT_RDWR)
        local_socket.close()
        return (False, ERROR_CMD)
    return (True, local_socket)


def transfer_in(local_socket, remote_socket):
    ''' local_socket - local socket '''
    ''' remote_socket - fileSocket '''
    local_socket_name = local_socket.getpeername()
    local_socket_address = local_socket_name[0]
    local_socket_port = local_socket_name[1]

    remote_socket_address = remote_socket.getHostname()
    remote_socket_port = str(remote_socket.getPort())
    print "[+] Starting transfer [%s:%s] => [%s:%s]" % (local_socket_address, local_socket_port, remote_socket_address, remote_socket_port)
    while True:
        ''' receive from local socket'''
        buff = local_socket.recv(0x1000)

        ''' if buffer not empty send to filesocket'''
        if buff:
            #remote_socket.send(handle(buff))
            remote_socket.send(buff)

        ''' if socket broke break '''
        if not buff or remote_socket.is_out_closed():
            print "[-] No data received from NETWORK! Breaking filesocket and remote connection..."
            remote_socket.close_in()
            print "[+] Closing connections! [%s:%s]" % (local_socket_address, local_socket_port)
            local_socket.close()
            break

        print "[+] %s:%d => %s:%s [%s]" % (local_socket_address, local_socket_port, remote_socket_address, remote_socket_port, repr(buff))
        print "[+] %s:%s => %s:%s => Length : [%d]" % (local_socket_address, local_socket_port, remote_socket_address, remote_socket_port, len(buff))



def transfer_out(remote_socket, local_socket):
    ''' Desccription : this function reads in all the data from the *.out file and closes it when all is read then sends data to local socket'''
    ''' remote_socket - the file socket '''
    ''' local_socket - local socket '''

    remote_socket_address = remote_socket.getHostname()
    remote_socket_port = remote_socket.getPort()

    local_socket_name = local_socket.getpeername()
    local_socket_address = local_socket_name[0]
    local_socket_port = local_socket_name[1]
    print "[+] Starting transfer [%s:%s] => [%s:%s]" % (remote_socket_address, remote_socket_port, local_socket_address, local_socket_port)

    while True:
        ''' receive from file socket'''
        buff = remote_socket.recv()

        ''' if buffer not empty send to local socket'''
        if buff:
            '''
            NOTE : this try except block is present only in transfer_out
                   since a socket.error occurs on send to dead socket
                   on recv the buffer is just empty but no error is triggered
            '''
            try:
                #local_socket.send(handle(buff))
                local_socket.send(buff)
            except socket.error as e:
                ''' if socket is closed we close our input too '''
                print "[-] socket error in transfer_out"
                print "[-] No data could be sent to socket"
                print "[-] Closing in connection on FILESOCKET "
                remote_socket.close_in()

        ''' if socket broke, break '''
        if (not buff) or remote_socket.is_in_closed():
            print "[-] No data received from FILESOCKET! Closing out connection on filesocket and breaking connection!"
            remote_socket.close_out()
            print "[+] Closing connection! [%s:%s]" % (local_socket, local_socket)
            local_socket.close()
            break





def handle(buffer):
    return buffer

if __name__ == "__main__":
    main()
