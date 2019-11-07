from unittest import TestCase
import sockser.socks_receiver as socres
from sockser.filesocket.filesocket import filesocket
import os
import socket
import time
import threading

class Test_socks_receiver(TestCase):

    @classmethod
    def setUpClass(self):

        ''' directory creation'''
        self.path = '/tmp/unittest/'
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        ''' file socket creation '''
        self.fsoc = filesocket()
        self.fsoc2 = filesocket(True)  # reverse socket
        self.hostname = '127.0.0.1'
        self.port = 65001
        self.timestamp = time.time()
        self.fsoc.connect((self.hostname, self.port), self.timestamp)
        self.fsoc2.connect((self.hostname, self.port), self.timestamp)

        ''' server_in creation '''
        max_connection = 10
        self.server_socket_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket_in.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket_in.bind((self.hostname,self.port))
        self.server_socket_in.listen(max_connection)

    def test_server(self):
        """ TODO """
        pass

    def test_socks_selection(self):
        """ TODO """
        pass

    def test_socks_request(self):
        """ TODO """
        pass

    def test_transfer_in(self):
        print ""
        print "test_transfer_in"

        ''' preparing data to send'''
        data = "azerza"

        data2 = "fffqqqfffqqq"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname,self.port))

        ''' prepare socket that will receive data '''
        local_socket,local_address = self.server_socket_in.accept()

        ''' starting transfer_in thread'''
        s = threading.Thread(target=socres.transfer_in,args=(local_socket, self.fsoc))
        s.start()

        ''' sending first piece of data'''
        self.ssoc_in.send(data)
        time.sleep(2)

        ''' checking if content received '''
        self.assertTrue(os.path.exists(self.fsoc.getInputStreamFilename()))
        self.assertTrue(os.path.exists(self.fsoc.getInputStreamFilenameSemaphore()))
        self.assertEqual(data, open(self.fsoc.getInputStreamFilename(), 'r').read())

        ''' sending second piece of data'''
        self.ssoc_in.send(data2)
        time.sleep(2)

        ''' check if data was not overwritten by new data '''
        self.assertEqual(data, open(self.fsoc.getInputStreamFilename(), 'r').read())

        ''' cleanup first data files '''
        os.remove(self.fsoc.getInputStreamFilename())
        os.remove(self.fsoc.getInputStreamFilenameSemaphore())

        time.sleep(2)

        ''' check if the second piece of data arrived '''
        self.assertEqual(data2, open(self.fsoc.getInputStreamFilename(), 'r').read())

        print "closing ssoc_in socket"
        self.ssoc_in.close()
        time.sleep(2)

        self.assertTrue(os.path.isfile(self.fsoc.getInputStreamFilename() + '.closed'))
        os.remove(self.fsoc.getInputStreamFilename() + '.closed')
        #self.assertTrue(os.path.isfile(self.fsoc.getOutputStreamFilename() + '.closed'))
        #os.remove(self.fsoc.getOutputStreamFilename() + '.closed')

    def test_transfer_out_data_transmission(self):
        print ""
        print "test_transfer_out_data_transmission"

        """ preparing data to receive """
        data = "msg data 1"
        data2 = "msg data 2"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare server socket that will send data (ssoc_in will received it)'''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_out thread'''
        s = threading.Thread(target=socres.transfer_out, args=(self.fsoc, local_socket))
        s.start()

        ''' writing first piece of data to file socket '''
        f = open(self.fsoc.getOutputStreamFilename(),'w')
        f.write(data)
        f.close()
        open(self.fsoc.getOutputStreamFilenameSemaphore(), 'w').close()

        '''waiting for transfer_out to process it'''
        time.sleep(2)

        ''' check if files were deleted after reading '''
        self.assertFalse(os.path.exists(self.fsoc.getOutputStreamFilename()))
        self.assertFalse(os.path.exists(self.fsoc.getOutputStreamFilenameSemaphore()))

        ''' checks if data matches what was .written in filesocket files '''
        socket_data = self.ssoc_in.recv(100)
        self.assertEqual(socket_data, data)

        ''' writing second piece of data to file socket'''
        f = open(self.fsoc.getOutputStreamFilename(), 'w')
        f.write(data2)
        f.close()

        ''' waiting for transfer_out to process it '''
        time.sleep(2)

        ''' checks whether data is not send before writing semaphore'''
        self.ssoc_in.settimeout(1)

        socket_data = ''
        try:
            socket_data = self.ssoc_in.recv(100)
        except:
            print 'timed out as it should'

        self.assertEqual('', socket_data)

        ''' writing '.written' lock for data to be read '''
        open(self.fsoc.getOutputStreamFilenameSemaphore(), 'w').close()

        ''' waiting for transfer_out to process it '''
        time.sleep(2)

        ''' reading data sent to socket '''
        socket_data = self.ssoc_in.recv(100)

        ''' waiting for transfer_out to process it '''
        time.sleep(2)

        ''' socket reads the second peace of data'''
        self.assertEqual(data2, socket_data)

        ''' check if files were deleted after receving '''
        self.assertFalse(os.path.exists(self.fsoc.getOutputStreamFilename()))
        self.assertFalse(os.path.exists(self.fsoc.getOutputStreamFilenameSemaphore()))

    def test_transfer_out_closing_on_filesocket_timeout(self):
        print ""
        print "test_transfer_out_closing_on_filesocket_timeout"

        ''' preparing data to receive '''
        data = "msg data 1"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare server socket that will send data (ssoc_in will received it)'''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_out thread'''
        s = threading.Thread(target=socres.transfer_out, args=(self.fsoc, local_socket))
        s.start()

        ''' we test the in filesocket closing (by writing the file socket close file to disk)'''
        ''' create "*.in.closed" file '''
        close_filename = self.fsoc.getInputStreamFilename() + '.closed'
        open(close_filename,'w').close()

        ''' write message to socket file '''
        f = open(self.fsoc.getOutputStreamFilename(), 'w')
        f.write(data)
        f.close()
        open(self.fsoc.getOutputStreamFilenameSemaphore(), 'w').close()

        ''' wait for transfer_out to process it '''
        time.sleep(2)

        ''' check if socket was "*.out.closed" was created '''
        self.assertTrue(os.path.exists(self.fsoc.getOutputStreamFilename() + '.closed'))


    def test_transfer_out_closing_on_network_socket_timeout(self):
        print ""
        print "test_transfer_out_closing_on_network_socket_timeout"

        ''' preparing data to receive '''
        data = "msg data 1"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare server socket that will send data (ssoc_in will received it)'''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_out thread'''
        s = threading.Thread(target=socres.transfer_out, args=(self.fsoc, local_socket))
        s.start()

        ''' we test SERVER SIDE socket close here. it can occur when we send data to a dead socket'''
        ''' close socket '''
        local_socket.close()

        ''' write message to socket file '''
        f = open(self.fsoc.getOutputStreamFilename(), 'w')
        f.write(data)
        f.close()
        open(self.fsoc.getOutputStreamFilenameSemaphore(), 'w').close()

        ''' wait for transfer_out to process it '''
        time.sleep(2)

        ''' check if socket was "*.out.closed" was created '''
        self.assertTrue(os.path.exists(self.fsoc.getOutputStreamFilename() + '.closed'))



    def test_handle(self):
        buffer = """zarefdezrazer"""
        self.assertEqual(buffer, socres.handle(buffer))

