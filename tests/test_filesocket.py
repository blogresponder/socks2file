from unittest import TestCase
from sockser.filesocket.filesocket import filesocket
import sockser.filesocket.filesocket_receiver_helper as h
import random
import os
import time
import threading

class TestFilesocket(TestCase):

    def setUp(self):
        self.path = '/tmp/unittest/'
        self.SOCKET_DIR = '/tmp/ensockserer/'
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        self.soc = filesocket()
        self.soc2 = filesocket(True)
        self.hostname = 'test.com'
        self.port = 1234
        self.timestamp = time.time()
        self.soc.connect((self.hostname, self.port), self.timestamp)
        self.soc2.connect((self.hostname, self.port), self.timestamp)

    def test_connect(self):
        self.assertEqual(self.soc.inputStreamFilename,self.SOCKET_DIR + self.hostname+':'+
                         str(self.port)+'.'+ str(int(self.timestamp))+'.in' )

        self.assertEqual(self.soc.outputStreamFilename,
                         self.SOCKET_DIR + self.hostname + ':' + str(self.port) + '.' + str(int(self.timestamp)) + '.out')

        self.assertEqual(self.soc.reverse,False)

        '''test reverse socket'''
        self.assertEqual(self.soc2.inputStreamFilename,self.SOCKET_DIR + self.hostname+':'+str(self.port)+'.'+str(int(self.timestamp))+'.out' )

        self.assertEqual(self.soc2.outputStreamFilename,
                         self.SOCKET_DIR + self.hostname + ':' + str(self.port) + '.' + str(int(self.timestamp)) + '.in')
        self.assertEqual(self.soc2.reverse,True)
        self.assertTrue(os.path.isdir(self.SOCKET_DIR))

    def test_getHostname(self):
        self.assertEqual(type(''),type(self.soc.getHostname()))
        self.assertEqual(self.hostname,self.soc.getHostname())

    def test_getPort(self):
        '''check type'''
        self.assertTrue(type(self.soc.getPort()), type(1111))
        '''check content'''
        self.assertTrue(self.soc.getPort(),self.port)

    def test_SocketDir(self):
        self.assertEqual(self.soc.getSocketDir(),self.SOCKET_DIR)

    def test_getInputStreamFilename(self):
        self.assertEqual(self.soc.getInputStreamFilename(),self.SOCKET_DIR +
                         self.hostname + ':' + str(self.port) + '.' + str(int(self.timestamp)) + '.in')

        '''reversed'''
        self.assertEqual(self.soc2.getInputStreamFilename(),
                         self.SOCKET_DIR + self.hostname + ':' + str(self.port) + '.' + str(
                             int(self.timestamp)) + '.out')

    def test_getOutputStreamFilename(self):
        self.assertEqual(self.soc.getOutputStreamFilename(),
                         self.SOCKET_DIR + self.hostname + ':' + str(self.port) + '.' + str(
                             int(self.timestamp)) + '.out')

        '''reversed'''
        self.assertEqual(self.soc2.getOutputStreamFilename(),
                         self.SOCKET_DIR + self.hostname + ':' + str(self.port) + '.' + str(
                             int(self.timestamp)) + '.in')
    def test_send(self):
        msg="send data"
        self.soc.send(msg)
        self.assertTrue(os.path.isfile(self.soc.getInputStreamFilename()))
        self.assertEqual(open(self.soc.getInputStreamFilename(),'r').read(), msg)
        msg2="send data reverse"
        self.soc2.send(msg2)
        self.assertTrue(os.path.isfile(self.soc2.getInputStreamFilename()))
        self.assertEqual(open(self.soc2.getInputStreamFilename(), 'r').read(), msg2)

        os.remove(self.soc.getInputStreamFilename())
        os.remove(self.soc2.getInputStreamFilename())

    def test_send_is_in_closed(self):

        ''' creating closed socket file'''
        close_in_filename = self.SOCKET_DIR + self.hostname + ':' + \
                         str(self.port) + '.' + str(int(self.timestamp)) + '.in.closed'
        self.soc.touch(close_in_filename)

        ''' sending data to closed file socket '''
        res = self.soc.send('test closed')
        print res
        self.assertFalse(res)
        self.assertFalse(os.path.isfile(self.soc.getInputStreamFilename()))
        close_out_filename = self.SOCKET_DIR + self.hostname + ':' + \
                         str(self.port) + '.' + str(int(self.timestamp)) + '.out.closed'
        self.soc2.touch(close_out_filename)
        res = self.soc2.send('test closed reverse')
        self.assertFalse(res)
        self.assertFalse(os.path.isfile(self.soc.getInputStreamFilename()))
        os.remove(close_in_filename)
        os.remove(close_out_filename)

    def test_recv(self):
        msg="sending test"
        self.soc.send(msg)
        self.assertTrue(os.path.isfile(self.soc.getInputStreamFilename()))
        data = self.soc2.recv()
        self.assertEqual(msg,data)
        self.assertFalse(os.path.isfile(self.soc.getInputStreamFilename()))


        msg = "sending test reverse"
        self.soc2.send(msg)
        self.assertTrue(os.path.isfile(self.soc2.getInputStreamFilename()))
        data = self.soc.recv()
        self.assertEqual(msg, data)
        self.assertFalse(os.path.isfile(self.soc2.getInputStreamFilename()))

    def test_touch(self):
        filename = 'test' + str(int(random.random() * 1000000))
        filepath = self.path + filename
        self.assertFalse(os.path.exists(filepath))
        self.soc.touch(filepath)
        self.assertTrue(os.path.exists(filepath))
        os.remove(filepath)

    def test_close_in(self):
        self.soc.close_in()
        close_in_filename = self.SOCKET_DIR + self.hostname + ':' + \
                             str(self.port) + '.' + str(int(self.timestamp)) + '.in.closed'

        self.assertTrue(os.path.exists(close_in_filename))
        os.remove(close_in_filename)

        '''reverse'''
        self.soc2.close_in()
        close_in_filename = self.SOCKET_DIR + self.hostname + ':' + \
                            str(self.port) + '.' + str(int(self.timestamp)) + '.out.closed'

        self.assertTrue(os.path.exists(close_in_filename))
        os.remove(close_in_filename)

    def test_close_out(self):
        self.soc.close_out()
        close_out_filename = self.SOCKET_DIR + self.hostname + ':' + \
                             str(self.port) + '.' + str(int(self.timestamp)) + '.out.closed'

        self.assertTrue(os.path.exists(close_out_filename))
        os.remove(close_out_filename)

        '''reverse'''
        self.soc2.close_out()
        close_out_filename = self.SOCKET_DIR + self.hostname + ':' + \
                            str(self.port) + '.' + str(int(self.timestamp)) + '.in.closed'

        self.assertTrue(os.path.exists(close_out_filename))
        os.remove(close_out_filename)

    def test_is_in_closed(self):
        self.soc.close_in()
        closed_file = self.soc.getInputStreamFilename() + '.closed'
        print closed_file

        self.assertTrue(os.path.exists(closed_file))
        self.assertTrue(self.soc.is_in_closed())

        os.remove(closed_file)

    def test_is_out_closed(self):
        self.soc.close_out()
        closed_file = self.soc.getOutputStreamFilename() + '.closed'
        print closed_file

        self.assertTrue(os.path.exists(closed_file))
        self.assertTrue(self.soc.is_out_closed())

        os.remove(closed_file)

    def tearDown(self):
        if os.path.isdir(self.path):
            os.rmdir(self.path)