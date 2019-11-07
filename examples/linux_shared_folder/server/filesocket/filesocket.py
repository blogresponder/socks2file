import os
import time
import filesocket_transmitter_helper as h


class filesocket(object):

    def __init__(self,reverse=False,socket_dir = '/tmp/file2socks'):

        self.SOCKET_DIR = socket_dir
        self.DELIMITER = '_'

        self.inputStreamFilename = None
        self.outputStreamFilename = None
        self.inputStreamFilenameSemaphore = None
        self.outputStreamFilenameSemaphore = None
        self.hostname = None
        self.port = None
        self.reverse = reverse
        self.timestamp = None
        self.timeout = 20 # used when receiving and sending data
        self.counter = 0 # used when receiving and sending data

    def connect(self,hostname_port_tuple,timestamp):
        ''' hostname_port_tuple - ("hostname",portnumber) '''
        ''' timestamp - identifier of the socket (None if it is a new connection, str of digits if it is an established connection'''
        self.hostname = hostname_port_tuple[0]
        self.port = int(hostname_port_tuple[1])

        ''' if new connection'''
        self.timestamp = str(int(timestamp))

        if not self.reverse:
            self.inputStreamFilename = self.SOCKET_DIR + self.hostname + self.DELIMITER + str(self.port) + '.' + self.timestamp + '.in'
            self.outputStreamFilename = self.SOCKET_DIR + self.hostname + self.DELIMITER + str(self.port) + '.' + self.timestamp + '.out'
        else:
            self.inputStreamFilename = self.SOCKET_DIR + self.hostname + self.DELIMITER + str(self.port) + '.' + self.timestamp + '.out'
            self.outputStreamFilename = self.SOCKET_DIR + self.hostname + self.DELIMITER + str(self.port) + '.' + self.timestamp + '.in'

        self.inputStreamFilenameSemaphore = self.inputStreamFilename + '.written'
        self.outputStreamFilenameSemaphore = self.outputStreamFilename + '.written'

        ''' create directory for fileSockets'''
        if not h.exists(self.SOCKET_DIR):
            h.make_dir(self.SOCKET_DIR)

        return self

    def getHostname(self):
        return self.hostname

    def getPort(self):
        return self.port

    def getSocketDir(self):
        return self.SOCKET_DIR

    def getInputStreamFilename(self):
        return self.inputStreamFilename

    def getOutputStreamFilename(self):
        return self.outputStreamFilename

    def getInputStreamFilenameSemaphore(self):
        return self.inputStreamFilenameSemaphore

    def getOutputStreamFilenameSemaphore(self):
        return self.outputStreamFilenameSemaphore

    def send(self,data):
        """
        Sends data to file socket
        :param data: data string to be sent over the file socket
        :return: return None if socket is closed and True if data was written to socket
        """

        ''' timeout counter '''
        #counter = 0

        while self.counter < self.timeout:
            ''' 1. check if socket is closed '''
            if self.is_in_closed() or self.counter == self.timeout-1:
                return False
            ''' 2. check if the file is not existent, if it isn't we create and write to it'''
            if not h.exists(self.inputStreamFilename) and not h.exists(self.inputStreamFilenameSemaphore):
                break
            time.sleep(1)
            self.counter += 1

        h.write(self.inputStreamFilename, data)
        h.write(self.inputStreamFilenameSemaphore,'')
        self.counter = 0
        return True

    def recv(self):
        """
        Recieves data from file socket
        NOTE : in this configuration the recv function is BLOCKING (as opposed to non-blocking)
                which seems normal since we do not want to read nor send empty strings to the other socket
        :return: returns string data or False if socket is closed or timed out
        """
        ''' timeout counter '''

        while self.counter < self.timeout:
            ''' check if file exists and writing has finished, if yes we do our job'''
            if h.exists(self.outputStreamFilename) and h.exists(self.outputStreamFilenameSemaphore):
                break
            ''' if sock is closed or timeout reached we return False'''
            if self.is_out_closed() or self.counter == self.timeout-1:
                return False
            ''' if nothing else, we sleep and increment timeout counter'''
            time.sleep(1)
            self.counter += 1

        result = h.read(self.outputStreamFilename)
        h.delete(self.outputStreamFilename)
        h.delete(self.outputStreamFilenameSemaphore)
        self.counter = 0

        return result

    def touch(self,filename):
        """
        creates empty file if it does not exist, does nothing otherwise
        :param filename: absolute path to filename to create
        :return:
        """
        if not h.exists(filename):
            h.write(filename, '')

    def close_in(self):
        """
        Close input stream.
        :return:
        """
        self.close(self.inputStreamFilename)

    def close_out(self):
        """
        Close input stream.
        :return:
        """
        self.close(self.outputStreamFilename)

    def close(self,filename):
        """
        Mark socket as closed by creating ".closed" file
        :param filename:
        :return:
        """
        closed_filename = filename + '.closed'
        self.touch(closed_filename)

        try:
            h.delete(filename)
        except:
            print "Error when deleting " + filename + " in close method"


    def is_closed(self):
        """
        Check whether input or output stream is closed
        :return:
        """
        return self.is_in_closed() or self.is_out_closed()

    def is_in_closed(self):
        """
        Checks whether the input stream has been closed
        :return: returns True if it is and false if it isn't
        """

        return h.exists(self.inputStreamFilename + ".closed")

    def is_out_closed(self):
        """
        Checks whether the output stream has been closed
        :return:
        """
        return h.exists(self.outputStreamFilename + ".closed")
