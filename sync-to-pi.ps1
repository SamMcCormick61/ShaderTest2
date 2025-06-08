# --- Configuration ---
$sourceFolder = "C:\Users\Sam\projects\ShadersGPU\Python\ShaderTest2"
$ftpHost = "192.168.1.222"
$remoteFolder = "ShaderTest2"  # The base remote folder on the FTP server
$username = "sam"
$password = "sampas1"
$interval = 10  # seconds

# --- State Tracking ---
# Use relative paths as keys to handle files with the same name in different folders.
$modTimes = @{}
# Track which remote directories have been created to avoid repeated checks.
$createdRemoteDirs = New-Object System.Collections.Generic.HashSet[string]

# --- Functions ---

# NEW FUNCTION: Ensures a directory path exists on the FTP server.
function Ensure-FtpDirectoryExists($remoteDirPath) {
    # If we've already created this directory in this session, skip.
    if ($createdRemoteDirs.Contains($remoteDirPath)) {
        return
    }

    $currentPath = ""
    $parts = $remoteDirPath.Split('/') | Where-Object { $_ } # Split and remove empty parts

    foreach ($part in $parts) {
        if ($currentPath.Length -gt 0) {
            $currentPath = "$currentPath/$part"
        } else {
            $currentPath = $part
        }

        $ftpUri = "ftp://$ftpHost/$currentPath"
        $request = [System.Net.FtpWebRequest]::Create($ftpUri)
        $request.Method = [System.Net.WebRequestMethods+Ftp]::MakeDirectory
        $request.Credentials = New-Object System.Net.NetworkCredential($username, $password)
        $request.UsePassive = $true
        $request.KeepAlive = $false

        try {
            # We don't need the response, just the action of creating the directory.
            $response = $request.GetResponse()
            $response.Close()
            Write-Host "Created remote directory: $currentPath"
        } catch [System.Net.WebException] {
            # Error 550 often means "file exists" or "permission denied".
            # We assume it exists if we get this error and continue.
            $ftpResponse = $_.Exception.Response
            if ($ftpResponse -and $ftpResponse.StatusCode -ne [System.Net.FtpStatusCode]::ActionNotTakenFileUnavailable) {
                 Write-Warning "Could not create directory '$currentPath'. FTP Status: $($ftpResponse.StatusCode) - $($ftpResponse.StatusDescription)"
            }
        } catch {
            Write-Warning "An unexpected error occurred creating directory '$currentPath': $_"
        }
    }
    # Add the full path to the set so we don't try to create it again.
    [void]$createdRemoteDirs.Add($remoteDirPath)
}


# MODIFIED FUNCTION: Uploads a file, creating its parent directory first.
function Upload-FileToFtp($localPath, $relativeFilePath) {
    # Convert Windows-style backslashes to FTP/URL-style forward slashes
    $remotePath = $relativeFilePath.Replace('\', '/')

    # Get the directory part of the path
    $remoteDir = [System.IO.Path]::GetDirectoryName($remotePath)

    # Ensure the remote directory exists before uploading
    if (-not [string]::IsNullOrEmpty($remoteDir)) {
        # The base remote folder must be prepended before creating the sub-directory
        Ensure-FtpDirectoryExists "$remoteFolder/$remoteDir"
    }

    $ftpUri = "ftp://$ftpHost/$remoteFolder/$remotePath"
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
        Write-Host "Uploaded: $relativeFilePath"
    } catch {
        Write-Host "Failed to upload: $relativeFilePath - $_"
    }
}


# --- Main Loop ---
Write-Host "Starting FTP sync monitor for '$sourceFolder'..."
while ($true) {
    # Get all files recursively from the source folder.
    Get-ChildItem -Path $sourceFolder -File -Recurse | ForEach-Object {
        $file = $_
        
        # Calculate the file's path relative to the source folder.
        # e.g., "my-image.png" or "subfolder1\data.json"
        $relativeFilePath = $file.FullName.Substring($sourceFolder.Length).TrimStart('\/')

        # --- FILTERING LOGIC ---
        # Check if the file is in a subfolder.
        if ($relativeFilePath.Contains('\')) {
            # Get the name of the top-level subfolder.
            $topLevelSubFolder = ($relativeFilePath.Split('\'))[0]
            
            # If the top-level subfolder does not start with a letter or number, skip this file.
            if ($topLevelSubFolder -notmatch '^[a-zA-Z0-9]') {
                return # 'return' here acts like 'continue' in a ForEach-Object block
            }
        }
        
        # Files directly in the root folder are always included.
        # Files in valid subfolders (like 'src' or '2023') are included.
        # Files in invalid subfolders (like '.github' or '_temp') are skipped.

        $modTime = $file.LastWriteTimeUtc

        # Check if the file is new or has been modified since the last upload.
        if (-not $modTimes.ContainsKey($relativeFilePath) -or $modTimes[$relativeFilePath] -lt $modTime) {
            # Use the relative path for both the upload destination and the tracking key.
            Upload-FileToFtp $file.FullName $relativeFilePath
            $modTimes[$relativeFilePath] = $modTime
        }
    }

    Start-Sleep -Seconds $interval
}