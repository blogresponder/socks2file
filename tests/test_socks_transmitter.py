from unittest import TestCase
import sockser.socks_transmitter as soc_transmitter
from sockser.filesocket.filesocket import filesocket
import socket
import os
import time
import threading

class TestServer(TestCase):

    @classmethod
    def setUpClass(self):
        ''' file socket creation '''

        self.fsoc = filesocket(reverse=True)
        self.hostname = '127.0.0.1'
        self.port = 65001
        self.timestamp = time.time()
        self.fsoc.connect((self.hostname, self.port), self.timestamp)

        ''' server_in creation '''
        max_connection = 10
        self.server_socket_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket_in.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket_in.bind((self.hostname, self.port))
        self.server_socket_in.listen(max_connection)

    def test_server(self):
        # TODO
        pass

    def test_socks_request(self):
        # TODO
        pass

    def test_transfer_in(self):
        print ""
        print "test_transfer_in"

        ''' prepare data to be sent '''
        data = "msg 1 data"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare socket that will receive data '''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_in thread'''
        s = threading.Thread(target=soc_transmitter.transfer_in,args=(self.fsoc, self.ssoc_in))
        s.start()

        ''' create file that will be sent '''
        f = open(self.fsoc.getOutputStreamFilename(), 'w')
        f.write(data)
        f.close()
        open(self.fsoc.getOutputStreamFilenameSemaphore(), 'w').close()

        time.sleep(2)
        response_data = local_socket.recv(100)

        self.assertEqual(data, response_data)

        ''' check if cleanup was done properly '''
        self.assertFalse(os.path.exists(self.fsoc.getOutputStreamFilename()))
        self.assertFalse(os.path.exists(self.fsoc.getOutputStreamFilenameSemaphore()))



    def test_transfer_in_filesocket_timeout(self):
        print ""
        print "test_transfer_in_filesocket_timeout"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare socket that will receive data '''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_in thread'''
        s = threading.Thread(target=soc_transmitter.transfer_in,args=(self.fsoc, self.ssoc_in))
        s.start()

        local_socket.close()

        time.sleep(24)

        self.assertTrue(os.path.exists(self.fsoc.getInputStreamFilename() + '.closed'))

    def test_transfer_in_on_socket_close(self):
        print ""
        print "test_transfer_on_socket_close"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare socket that will receive data '''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_in thread'''
        s = threading.Thread(target=soc_transmitter.transfer_in,args=(self.fsoc, self.ssoc_in))
        s.start()

        """ closing socket on the SERVER"""
        local_socket.close()

        """ sending data to it """
        data = "dead socket msg"

        ''' create file that will be sent '''
        f = open(self.fsoc.getOutputStreamFilename(), 'w')
        f.write(data)
        f.close()
        open(self.fsoc.getOutputStreamFilenameSemaphore(), 'w').close()

        time.sleep(2)

        ''' create file that will be sent '''
        f = open(self.fsoc.getOutputStreamFilename(), 'w')
        f.write(data)
        f.close()
        open(self.fsoc.getOutputStreamFilenameSemaphore(), 'w').close()

        time.sleep(2)

        self.assertTrue(os.path.exists(self.fsoc.getInputStreamFilename() + '.closed'))

    def test_transfer_out(self):
        print ''
        print 'test_transfer_out'

        ''' prepare data to be sent '''
        data = "msg transfer_out data"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare socket that will receive data '''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_out thread'''
        s = threading.Thread(target=soc_transmitter.transfer_out, args=(self.ssoc_in, self.fsoc))
        s.start()

        local_socket.send(data)

        time.sleep(2)

        self.assertTrue(os.path.exists(self.fsoc.getInputStreamFilename()))
        self.assertTrue(os.path.exists(self.fsoc.getInputStreamFilenameSemaphore()))

        f = open(self.fsoc.getInputStreamFilename(), 'r')
        response_data = f.read()
        f.close()

        self.assertEqual(data, response_data)

        ''' cleanup mess'''
        os.remove(self.fsoc.getInputStreamFilename())
        os.remove(self.fsoc.getInputStreamFilenameSemaphore())

    def test_transfer_out_network_socket_timeout(self):
        print ''
        print 'test_transfer_out_socket_timeout'

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare socket that will receive data '''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_out thread'''
        s = threading.Thread(target=soc_transmitter.transfer_out, args=(self.ssoc_in, self.fsoc))
        s.start()

        local_socket.close()

        time.sleep(4)

        self.assertTrue(os.path.exists(self.fsoc.getOutputStreamFilename() + '.closed'))

    def test_transfer_out_filesocket_timeout(self):
        print ''
        print 'test_transfer_out_filesocket_timeout'

        data = "message to dead filesocket"

        ''' regular socket_in creation '''
        self.ssoc_in = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssoc_in.connect((self.hostname, self.port))

        ''' prepare socket that will receive data '''
        local_socket, local_address = self.server_socket_in.accept()

        ''' starting transfer_out thread'''
        s = threading.Thread(target=soc_transmitter.transfer_out, args=(self.ssoc_in, self.fsoc))
        s.start()

        time.sleep(2)

        local_socket.send(data)

        ''' we test the in filesocket closing (by writing the file socket close file to disk)'''
        ''' create "*.out.closed" file '''
        close_filename = self.fsoc.getInputStreamFilename() + '.closed'
        open(close_filename,'w').close()

        time.sleep(2)

        ''' check if socket was "*.in.closed" was created '''
        self.assertTrue(os.path.exists(self.fsoc.getOutputStreamFilename() + '.closed'))


    def test_poll_open_connections(self):
        """ creation of valid '*.in' file """
        connection_filename = soc_transmitter.SOCKSER_DIR + "polling_test.in"
        connection_basename = os.path.basename(connection_filename)
        open(connection_filename,'w').close()
        """ check if funtion parses the results correctly """
        soc_transmitter.poll_open_connections()
        print soc_transmitter.SOCKSER_DIR
        print soc_transmitter.OPEN_CONNECTIONS
        self.assertIn(connection_basename, soc_transmitter.OPEN_CONNECTIONS)

        """ creation of invalid file 2 """
        connection_filename2 = soc_transmitter.SOCKSER_DIR + "poll_test.insqdf"
        open(connection_filename2, 'w').close()
        """ check if funtion parses the results correctly"""
        soc_transmitter.poll_open_connections()
        self.assertNotIn(connection_filename2, soc_transmitter.OPEN_CONNECTIONS)

        """ creation of invalid file 3 """
        connection_filename3 = soc_transmitter.SOCKSER_DIR + "poll_test.out"
        open(connection_filename3, 'w').close()
        """ check if funtion parses the results correctly"""
        soc_transmitter.poll_open_connections()
        self.assertNotIn(connection_filename3, soc_transmitter.OPEN_CONNECTIONS)

        """ creation of invalid file 4 """
        connection_filename4 = soc_transmitter.SOCKSER_DIR + "poll_test.outfdsq"
        connection_basename4 = os.path.basename(connection_filename4)
        open(connection_filename4, 'w').close()
        """ check if funtion parses the results correctly"""
        soc_transmitter.poll_open_connections()
        self.assertNotIn(connection_filename4, soc_transmitter.OPEN_CONNECTIONS)

        """ creation of valid '*.in' file """
        connection_filename5 = soc_transmitter.SOCKSER_DIR + "polling_test2.in"
        connection_basename5 = os.path.basename(connection_filename5)
        open(connection_filename5,'w').close()
        """ check if funtion parses the results correctly"""
        soc_transmitter.poll_open_connections()
        self.assertIn(connection_basename5,soc_transmitter.OPEN_CONNECTIONS)

        os.remove(connection_filename)
        os.remove(connection_filename2)
        os.remove(connection_filename3)
        os.remove(connection_filename4)
        os.remove(connection_filename5)

    def test_handle(self):
        buffer = """zarefdezrazer"""
        self.assertEqual(buffer, soc_transmitter.handle(buffer))
