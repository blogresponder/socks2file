
$SOCKS_DIR = "E:\socks"
$PORT_DELIM = '_'
$timeout = 20

function Get-IpAddress{
    param($ip)
    IF ($ip -as [ipaddress]){
        return $ip
    }else{
        $ip2 = [System.Net.Dns]::GetHostAddresses($ip)[0].IPAddressToString;
        Write-Host "$ip resolved to $ip2"
    }
    return $ip2
}

$communicate_in=[scriptblock]{
    param ($DNS_hostname,$tcpConnection,$SOCKS_DIR,$PORT_DELIM,$timeout,$timestamp)

    $tcpStream = $tcpConnection.GetStream()

    #$server = $tcpConnection.Client.RemoteEndpoint.Address.IPAddressToString
    $port = $tcpConnection.Client.RemoteEndpoint.Port

    $iStreamFilename = $SOCKS_DIR + '\' + $DNS_hostname + $PORT_DELIM + $port + '.' + $timestamp + '.in'
    $iStreamWrittenFilename = $iStreamFilename + '.written'
    $iStreamClosedFilename = $iStreamFilename + '.closed'

    while ($tcpConnection.Connected)
    {

        $timeoutCounter = 0
        # check for input existence and wait until it comes, timeouts after n-tries
        while(-Not (Test-Path $iStreamWrittenFilename) -and $timeoutCounter -lt $timeout)
        {
            Start-Sleep -Seconds 1
            $timeoutCounter++
        }

        # check if timeout was not reached
        if($timeoutCounter -eq $timeout)
        {
            Write-Output 'communcation_in timeout! Breaking.'
            break
        }

        # get data from file
        #$data = Get-Content -Path $iStreamFilename

        $binaryReader = New-Object System.IO.BinaryReader([System.IO.File]::Open($iStreamFilename, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        )

        $data = $binaryReader.ReadBytes(0x1000)

        $binaryReader.close()


        # send data
        $binaryWriter = New-Object System.IO.BinaryWriter $tcpStream
        $data[0..0x1000] | ForEach-Object{ $binaryWriter.Write( $_ ) }
        #$writer.Write($data) | Out-Null

        

        start-sleep -Seconds 1

        Remove-Item -Path $iStreamFilename
        Remove-Item -Path $iStreamWrittenFilename
    }

    $tcpConnection.Close()

}

$communicate_out=[scriptblock]{
    param ($DNS_hostname,$tcpConnection,$SOCKS_DIR,$PORT_DELIM,$timeout,$timestamp)
    $tcpStream = $tcpConnection.GetStream()
    $reader = New-Object System.IO.StreamReader($tcpStream)


    $buffer = new-object System.Byte[] 0x1000

    #$server = $tcpConnection.Client.RemoteEndpoint.Address.IPAddressToString
    $port = $tcpConnection.Client.RemoteEndpoint.Port

    $oStreamFilename = $SOCKS_DIR + '\' + $DNS_hostname + $PORT_DELIM + $port + '.' + $timestamp + '.out'
    $oStreamWrittenFilename = $oStreamFilename + '.written'
    $oStreamClosedFilename = $oStreamFilename + '.closed'
    

    while ($tcpConnection.Connected)
    {
        $timeoutCounter = 0
        # check for lack of output file existence and wait until it comes is read and deleted by the other side, timeouts after n-tries
        while((Test-Path $oStreamWrittenFilename) -and $timeoutCounter -lt $timeout)
        {
            Start-Sleep -Seconds 1
            $timeoutCounter++
        }

        # check if timeout was not reached
        if($timeoutCounter -eq $timeout)
        {
            Write-Output 'communcation_out timeout! Breaking.'
            break
        }

        # recv data
        $response_length = $tcpStream.Read($buffer, 0, 0x1000)

        if ($response_length -gt 0)
        {
            # Creating fileStream and binaryWriter
            $fileStream = New-Object IO.FileStream $oStreamFilename, 'Create'
            $binaryWriter = New-Object System.IO.BinaryWriter $fileStream

            # Write data to file
            $buffer[0..($response_length-1)] | ForEach-Object { $binaryWriter.Write($_) }

            # Close file descriptors
            $fileStream.close()
            $binaryWriter.close()

            # Write ".written" file
            Copy-Item -Path $oStreamFilename -Destination $oStreamWrittenFilename
            Set-Content -Path $oStreamWrittenFilename -Value ''
        }

        start-sleep -Seconds 1
    }

    # Close connection
    Set-Content -Path $oStreamClosedFilename -Value ''
    $tcpConnection.Close()

}

# check for existence of folder
if (-Not (Test-Path $SOCKS_DIR))
{
    New-Item -Path $SOCKS_DIR -ItemType Directory
}

Write-Output "Starting polling files in the following folder:"
Write-Output $SOCKS_DIR
Write-Output ""
$OPEN_CONNECTIONS = @()
$MANAGED_CONNECTIONS = @()

while($true)
{
    $inSockets = Get-ChildItem $SOCKS_DIR | Where-Object {$_.Extension -eq '.in'} 
    
    foreach ($i in $inSockets)
    {
        if(!$MANAGED_CONNECTIONS.Contains($i.FullName))
        {
            $OPEN_CONNECTIONS += $i.FullName
        }
    }

    <# launch socket jobs#>
    foreach ($i in $OPEN_CONNECTIONS)
    {
        if (!$MANAGED_CONNECTIONS.Contains($i))
        {
            $MANAGED_CONNECTIONS += $i

            Write-Output 'Current OPEN_CONNECTIONS :'
            Write-Output $OPEN_CONNECTIONS
        
            Write-Output 'Current MANAGED_CONNECTIONS :'
            Write-Output $MANAGED_CONNECTIONS

            $leaf = Split-Path -path $i -Leaf

            # prepare and launch the job

            # Get Host
            # Note : DNS hostname will be needed later to create an output file with the correct name.
            $DNS_hostname = $leaf.split($PORT_DELIM)[0]
            
            $server = Get-IpAddress($DNS_hostname)


            # Get Port
            $port = $leaf.split($PORT_DELIM)[1].split('.')[0]
            
            # Get Timestamp
            $timestamp = $leaf.split($PORT_DELIM)[1].split('.')[1]
            
            # Start connection (shared by the following two jobs)
            try {
                $tcpConnection = New-Object System.Net.Sockets.TcpClient($server, $port)
            }
            catch {
                Write-Output "Error openning connection to $Server port $Port."
            }
            
            # start job communicate_in
            $pin = [PowerShell]::Create()
            $null = $pin.AddScript($communicate_in).AddParameters(@($DNS_hostname, $tcpConnection,$SOCKS_DIR,$PORT_DELIM,$timeout,$timestamp))
            $job_in = $pin.BeginInvoke()

            # start job communicate_out
            $pout = [PowerShell]::Create()
            $null = $pout.AddScript($communicate_out).AddParameters(@($DNS_hostname,$tcpConnection,$SOCKS_DIR,$PORT_DELIM,$timeout,$timestamp))
            $job_out = $pout.BeginInvoke()
        }
    }
 
    Start-Sleep -Seconds 1
}
