from unittest import TestCase
import sockser.filesocket.filesocket_receiver_helper as helper
import os
import random
import string
import time
import threading

class TestFilesocket_reciever_helper(TestCase):

    def setUp(self):
        self.path = '/tmp/test' + str(int(random.random() * 1000000))
        self.data = random.choice(string.ascii_letters) *random.randrange(15)
        f = open(self.path,'w')
        f.write(self.data)
        f.close()
        print "data:" + self.data
        print "len(data):" + str(len(self.data))

    def tearDown(self):
        print "removing test file : " + self.path
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_write(self):
        print ""
        print "test_write"
        helper.write(self.path,self.data)
        self.assertTrue(os.path.isfile(self.path))
        self.assertTrue(len(self.data) == len(open(self.path,'r').read()))
        os.remove(self.path)

    def test_read(self):
        print ""
        print "test_read"
        res = helper.read(self.path)
        self.assertEqual(res, self.data)

    def test_delete(self):
        print ""
        print "test_delete"
        helper.delete(self.path)

        self.assertFalse(os.path.exists(self.path))

    def test_exists(self):
        print ""
        print "test_exists"
        res = helper.exists('/etc/')
        self.assertTrue(res)

        res = helper.exists('/etc/passwd')
        self.assertTrue(res)

        res = helper.exists('/dsqfdsqf/dsfazsqdfaezfdsf')
        self.assertFalse(res)
        print "exists tests passed"

    def _delete_lock_delay(self,lock_filename,delay):
        time.sleep(delay)
        os.remove(lock_filename)
