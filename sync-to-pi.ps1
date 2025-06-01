$sourceFolder = "C:\Users\Sam\projects\ShadersGPU\Python\ShaderTest2"
$ftpHost = "192.168.1.222"
$remoteFolder = "ShaderTest2"  # relative to FTP root
$username = "sam"
$password = "sampas1"
$interval = 10  # seconds

# Track last modified times
$modTimes = @{}

function Upload-FileToFtp($localPath, $fileName) {
    $ftpUri = "ftp://$ftpHost/$remoteFolder/$fileName"
    $request = [System.Net.FtpWebRequest]::Create($ftpUri)
    $request.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
    $request.Credentials = New-Object System.Net.NetworkCredential($username, $password)
    $request.UseBinary = $true
    $request.UsePassive = $true
    $request.KeepAlive = $false

    try {
        $fileContent = [System.IO.File]::ReadAllBytes($localPath)
        $request.ContentLength = $fileContent.Length

        $requestStream = $request.GetRequestStream()
        $requestStream.Write($fileContent, 0, $fileContent.Length)
        $requestStream.Close()

        $response = $request.GetResponse()
        $response.Close()
        Write-Host "Uploaded: $fileName"
    } catch {
        Write-Host "Failed to upload: $fileName - $_"
    }
}

while ($true) {
    Get-ChildItem -Path $sourceFolder -File | Where-Object {
        -not $_.Name.StartsWith(".")
    } | ForEach-Object {
        $fileName = $_.Name
        $modTime = $_.LastWriteTimeUtc

        if (-not $modTimes.ContainsKey($fileName) -or $modTimes[$fileName] -lt $modTime) {
            Upload-FileToFtp $_.FullName $fileName
            $modTimes[$fileName] = $modTime
        }
    }

    Start-Sleep -Seconds $interval
}
