#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import threading
import sys
import os
import time
from filesocket import filesocket

SOCKSER_DIR = ''
OPEN_CONNECTIONS=[]
MANAGED_CONNECTIONS=[]
PORT_DELIMITER = '_'

def main():
    global SOCKSER_DIR
    if len(sys.argv) < 2:
        print "Usage : "
        print "\tpython %s [TMP_DIR]" % (sys.argv[0])
        print "Example : "
        print "\tpython %s /tmp/file2socks/" % (sys.argv[0])
        exit(1)

    SOCKSER_DIR = sys.argv[1]

    if SOCKSER_DIR[-1] != '/':
        SOCKSER_DIR += '/'

    print "Sockser dir :" + SOCKSER_DIR

    server()

def server():
    try:

        print '[+] Fake server started...'
        while True:
            time.sleep(1)
            poll_open_connections()

            global OPEN_CONNECTIONS
            global MANAGED_CONNECTIONS

            """ Loop that makes sure that new connections is added to MANAGER_CONNECTIONS"""
            for conn_file in OPEN_CONNECTIONS:
                """ if the connection is a NEW connection (not MANAGED)"""
                if conn_file not in MANAGED_CONNECTIONS:
                    MANAGED_CONNECTIONS.append(conn_file)
                    result = socks_request(conn_file)
                    if not result[0]:
                        print "[-] socks request error!"
                        break
                    local_socket, remote_socket = result[1]


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

def socks_request(sockser_in):
    '''sockser_in - sockser_in filename'''

    # READ in local ip and port based on filenames
    dst_address = sockser_in.split(PORT_DELIMITER)[0]
    dst_port = int(sockser_in.split(PORT_DELIMITER)[1].split('.')[0])
    timestamp = str(int(sockser_in.split(PORT_DELIMITER)[1].split('.')[1]))

    print "[+] IPv4 : %s" % (dst_address)
    print "[+] Port : %s" % (dst_port)

    # SETTING UP FILENAME instead of preparing socket
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_socket = filesocket.filesocket(True, SOCKSER_DIR)

    try:
        print "[+] Connecting : %s:%s" % (dst_address, dst_port)
        remote_socket.connect((dst_address, dst_port))

        local_socket.connect((dst_address,dst_port),timestamp)

        print "[+] Tunnel connected! Tranfering data..."
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

    return (True, local_socket)

def transfer_in(local_socket, remote_socket):
    ''' local_socket - file socket '''
    ''' remote_socket - socket to target'''

    local_socket_address = local_socket.getHostname()
    local_socket_port = local_socket .getPort()

    remote_socket_name = remote_socket.getpeername()
    remote_socket_address = remote_socket_name[0]
    remote_socket_port = remote_socket_name[1]

    print local_socket_address
    print local_socket_port

    print "[+] Starting transfer [%s:%s] => [%s:%s]" % (local_socket_address, local_socket_port, remote_socket_address, remote_socket_port)
    while True:
        buff = local_socket.recv()
        if local_socket.is_out_closed() or not buff:
            print "[-] No data received FROM FILE! Breaking..."
            local_socket.close_in()    # it is OUT because it is in reverse (so we are closing *.in)

            ''' cleanup the connection from managed connections '''
            cleanup_connections(local_socket.getOutputStreamFilename())

            break
        if buff:
            ''' if file buffer is empty no need to send anything'''
            print "[+] %s:%s => %s:%s => Length : [%d]" % (local_socket_address, local_socket_port, remote_socket_address, remote_socket_port, len(buff))
            # SEND to local SOCKS client
            print 'sending buffer'
            print handle(buff)
            try:
                remote_socket.send(handle(buff))
            except:
                ''' if network socket is closed we close our input too '''
                print "[-] socket error in transfer_in"
                print "[-] No data could be sent to network final server socket"
                print "[-] Closing out connection on FILESOCKET "
                local_socket.close_out()
        #time.sleep(1)

    print "[+] Closing connecions! [%s:%s]" % (remote_socket_address, remote_socket_port)
    remote_socket.close()

def transfer_out(remote_socket, local_socket):
    ''' remote_socket - socket to target'''
    ''' local_socket - file socket '''

    remote_socket_name = remote_socket.getpeername()
    remote_socket_address = remote_socket_name[0]
    remote_socket_port = remote_socket_name[1]

    local_socket_address = local_socket.getHostname()
    local_socket_port = local_socket.getPort()
    print "[+] Starting transfer [%s:%s] => [%s:%s]" % (remote_socket_address, remote_socket_port, local_socket_address, local_socket_port)


    while True:
        ''' receive from remote socket'''
        buff = remote_socket.recv(0x1000)

        ''' if buffer not empty send to filesocket'''
        if buff:
            local_socket.send(handle(buff))

        ''' if socket broke break '''
        if not buff or local_socket.is_in_closed():
            print "[-] No data received from NETWORK! Breaking filesocket and connection!"
            local_socket.close_out()
            print "[+] Closing connecions! [%s:%s]" % (remote_socket_address, remote_socket_port)
            remote_socket.close()

            ''' cleanup the connection from managed connections '''
            cleanup_connections(local_socket.getOutputStreamFilename())

            break

        # print "[+] %s:%d => %s:%d [%s]" % (src_address, src_port, dst_address, dst_port, repr(buff))
        print "[+] %s:%s => %s:%s => Length : [%d]" % (remote_socket_address, remote_socket_port, local_socket_address, local_socket_port, len(buff))

    remote_socket.close()

    print "[+] Closing connecions! [%s:%s]" % (local_socket_address, local_socket_port)
    #local_socket.close()

def poll_open_connections():
    """
    List the content of folder SOCKSER_DIR and appends to array OPEN_CONNECTIONS all filenames
    ending with '.in'
    :return: doesn't return anything, stores data in OPEN_CONNECTIONS but ONLY the FILENAME
             NOT the FULL PATH
    """
    global OPEN_CONNECTIONS
    if os.path.exists(SOCKSER_DIR):
        for filename in os.listdir(SOCKSER_DIR):
            """ we make sure with the second condition that the same file is not added twice"""
            if filename[-3:] == '.in' and filename not in OPEN_CONNECTIONS:
                OPEN_CONNECTIONS.append(filename)

def cleanup_connections(connection_in_path):
    '''
    Method that performs cleaning up after socket is closed.
    :param connection_in_path:
    :return:
    '''
    global MANAGED_CONNECTIONS
    global OPEN_CONNECTIONS
    root_filename = connection_in_path[-3]

    try:
        os.remove(root_filename + '.in')
    except:
        print root_filename + ".in already deleted"
    try:
        os.remove(root_filename + '.out')
    except:
        print root_filename + ".out already deleted"
    try:
        os.remove(root_filename + '.in.closed')
    except:
        print root_filename + ".in.closed already deleted"
    try:
        os.remove(root_filename + '.in.written')
    except:
        print root_filename + ".in.written already deleted"
    try:
        os.remove(root_filename + '.out.closed')
    except:
        print root_filename + ".out.closed already deleted"
    try:
        os.remove(root_filename + '.out.written')
    except:
        print root_filename + ".out.closed already deleted"
    try:
        OPEN_CONNECTIONS.remove(os.path.basename(connection_in_path))
    except:
        print os.path.basename(connection_in_path) + " already removed from OPEN_CONNECTIONS"
    try:
        MANAGED_CONNECTIONS.remove(os.path.basename(connection_in_path))
    except:
        print os.path.basename(connection_in_path) + " already removed from MANAGED_CONNECTIONS"

def handle(buff):
    return buff

if __name__ == "__main__":
    main()
