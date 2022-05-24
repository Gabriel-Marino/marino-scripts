# Directory path where Batch is being executed;
$dirPATH = Get-Location
$logfile = "$dirPATH\log.txt"

try {
    # Enabling the Windows Subsystem for Linux;
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

    # Enabling Virtual Machine feature;
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

    # Downloading the Linux kernel update package;
    $WebClient = New-Object System.Net.WebClient
    $WebClient.DownloadFile("https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi", "$dirPATH\wsl_update_x64.msi")

    # Executing the Linux kernel update package;
    Start-Process -ArgumentList -NoProfile -File "$dirPATH\wsl_update_x64.msi" -Wait
    # Deleting the Linux kernel update package;
    Remove-Item -Path "$dirPATH\wsl_update_x64.msi"

    # Setting WSL 2 as your default version;
    wsl --set-default-version 2

    Write-Output "Made It"
    Restart-Computer -Confirm
} catch {
    Write-Output "Something goes wrong! See Log.txt"
    Out-File -Force -FilePath $logfile -InputObject $Error -Encoding utf8 -Width 128
}