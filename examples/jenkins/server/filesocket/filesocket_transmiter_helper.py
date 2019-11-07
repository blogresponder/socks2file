import os
import time
from base64 import b64decode, b64encode

def write(filename,data):
    """
    writes data to file using the implemented method
    creates the file if the file does not exist
    if the file exists it appends to its content

    :param filename: full path to the file to write
    :type filename: string
    :param data: data to be written to file
    :type data: string
    :return:
    """

    f = open(filename,'w')

    print "WRITE : " + b64encode(data)
    print "filename : " + filename
    f.write(b64encode(data))
    f.flush()
    f.close()


def read(filename):
    """
    Reads the data from filename
    :param filename: absolute path to file to read
    :type filename: string
    :return: content of read file
    """


    print "READ : " + b64decode(open(filename,'r+').read())
    print "filename : " + filename

    return b64decode(open(filename,'r+').read())


def make_dir(dirname):
    """
    Creates a directory
    :param dirname: full path to the directory to create
    :return:
    """
    os.mkdir(dirname)


def exists(filename):
    """
    checks weather a directory or file of filename exists
    :param filename: full path to filename to check the existence of
    :return:
    """

    print "EXIST : " + filename

    return os.path.exists(filename)


def delete(filename):
    """
    Deletes file
    :param filename: absolute path to file to delete.
    :return:
    """

    print "DELETE : " + filename
    os.remove(filename)

