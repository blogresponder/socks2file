# Socks2File

## Description

This project is an implementation of the SOCKS5 proxy which makes all of its communication go through temporary files (for both Linux using *Python2.7* and Windows using *Powershell*).

*DISCLAIMER: This method is slow and is not optimal for most uses. In most cases there are smarter, better and faster ways to proxify traffic to the internal network. In some cases, this tool may need to be adapted to work with some new use case or attack scenario, but it designed to limit the code modifications to the strict minimum (see "Other Scenarios" for more details).*

The initial use case of this was to be able to open a SOCKS5 proxy communication in Red Team scenarios in highly constrained DMZ networks where it is **not possible to write files directly to webroot** (in which case tools like ReGeorge proxyfing tools can be used), and where it is **not possible to connect back to an outside server** in which case forwarding rules could be established.

The following **requirements** need to be fulfilled in order for this tool to work :
- a command execution is already present on the server (*for instance through web application vulnerability*)
- file read is possible (from a some directory, for instance */tmp*)
- file write (in a directory, for instance */tmp*) is possible
- file delete (from a directory, for instance */tmp*) is possible
- file existence checking (in a directory, for instance */tmp*) is possible

Following is a simple explanation chart explaining the concept :

<p align="center">
  <img src="https://github.com/blogresponder/socks2file/raw/master/screenshots/receiver_transmitter_concept.png">
</p>

As can be seen, the **socks_receiver** script opens a SOCKS proxy locally on the attacker's computer, the **socks_transmitter** script is executed on the attacked host. Both of these script will perform polling of the content of the chosen temporary folder in order to interconnect the input temporary files to TCP sockets on the DMZ and send back the TCP responses from these sockets back to temporary files read by the **socks_receiver** script.
 
To achieve this task a FileSocket API was implemented for this purpose that allows to vaguely mimic the behavior of regular TCP sockets.

## Use cases
This tool could be adapted to various use cases. The main objective was to ensure as much cross-platform portability as possible with the use of temporary files. Among others, following use cases could be foreseen :
- SOCKS5 proxying through HTTP
- SOCKS5 proxying through SMB share
- SOCKS5 proxying through FTP share
- multichannel SOCKS5 proxying (for instance HTTP used for writing and FTP for reading or any other combination)

## Quick start 

In any case, the **transmitter** script should work out-of-the-box. The *Python2.7* script does not include any non standard packages (it uses only the *FileSocket API* embedded in this project and *socket* for TCP connections), the *Powershell* transmitter script was tested on Windows 10, Powershell version 5.1.17763.592 **but** should work on mostly any Powershell 5 and shouldn't require much adaptation for other versions.

The **receiver** script needs some adjustments

### Out-Of-The-Box examples
Some examples were implemented which should work more or less out of the box.

#### Linux shared folder (through SMB or FTP)
- mount the remote shared folder on your local machine (for instance to */tmp/socks*)
##### Receiver
- launch the server like so :
```
python ./examples/linux_shared_folder/client/socks_receiver.py 127.0.0.1 <PORT_NUMBER> <path_to_directory_to_create_socks_files_in>
```
##### Transmitter
- upload the *examples/linux_shared_folder/server/* directory to the vulnerable server
- launch the *transmitter* like so :
```
python ./socks_transmitter.py <path_to_directory_to_create_socks_files_in>
```


#### Windows shared folder (through SMB or FTP)
- mount the remote shared folder on your local machine (for instance to */tmp/socks*)
##### Receiver
- launch the server like so :
```
python ./examples/linux_shared_folder/client/socks_receiver.py 127.0.0.1 <PORT_NUMBER> <path_to_directory_to_create_socks_files_in>
```
##### Transmitter
- change the *SOCKS_DIR* path in the Powershell script adjust the path to the temporary files in the script
```powershell
$SOCKS_DIR = "C:\Users\user\TEMP\socks\"
```
- upload the *examples/windows_shared_folder/server/socks_transmitter.ps1* directory to the vulnerable server
- launch the transmitter like so :
```
./socks_transmitter.ps1
```
NOTE: This execution could be blocked by Powershell Execution policy. This can be for instance fixed with
 the following if you have the right to execute it:
```powershell
Set-ExecutionPolicy Bypass -Scope CurrentUser
```
Other bypasses could be possible such as streaming the file into Powershell.

#### Jenkins
##### Receiver
- connect to the Jenkins console and find the following values needed for the configuration :
    - JSESSIONID cookie name (such as for instance : "JSESSIONID.18ebfca1")
    - JSESSIONID cookie value (such as for instance : "node0n406bkejxcgainve10s3xpr24.node0")
    - Jenkins_Crumb token (such as for instance : "01b253c1d5ea4f555fe083cb6718e8a2ed727530e7b49ca145eab66bac08b42d")

- write the previously found values to the **examples/jenkins/client/config.yaml** file.
- run the receiver as follows :
```
python ./socks2file/examples/jenkins/client/socks_receiver.py 127.0.0.1 <PORT_NUMBER> <path_to_directory_to_create_socks_files_in>
```

##### Transmitter
- upload the **./socks2file/examples/jenkins/server/** directory to the Jenkins server
- launch the transmitter as follows
```
python ./socks_transmitter.py <path_to_directory_to_create_socks_files_in>
```

### Other scenarios
In other real-world scenarios, the FileSocket API code needs *5 small adjustments*. In fact, the only thing that needs to be adjusted in most cases is the *filesocket_receiver_helper.py* file. This file is well documented and holds only 5 methods :

- write(filename,data)
- read(filename)
- make_dir(dirname)
- exists(filename)
- delete(filename)

These methods will define how the *receiver* script will be able to access and create temporary files for use by the *transmitter* script.

## Known issues
- the *.closed* and *.written* files stay in the temporary directory. Until now, this was done for debugging purposes. This may be corrected in the future.
- verbose debug information is displayed on terminal when scripts are running. Those can be deleted in the future versions or verbosity option could be added.
- the Powershell transmitter script can hang in some rare cases which can make a specific TCP connection timeout and drop.

## Reference
The SOCKS5 implementation was based on code found on WangYihang gist 
	https://gist.github.com/WangYihang/e360574f78eb8a30671536e2e4c2fd59#file-socks-proxy-simple-py

