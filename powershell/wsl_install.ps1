<#
    .Description
        Enable, Download and Install Windows Subsystem for Linux (WSL);

    .Paramaters
        None;

    .Notes
        This script run following the instructions given here: https://docs.microsoft.com/en-us/windows/wsl/install-win10

    .Notes
            Probabily will be needed to change some execution policies in the console where te script will be running,
        so i recommend using the following command (line below w/o exclamation) on the terminal before executing the script
        !   Set-ExecutionPolicy -Confirm -ExecutionPolicy Bypass -Force -Scope CurrentUser

#>

# Directory path where Batch is being executed;
$dirPATH = Get-Location
$logfile = "$dirPATH\log-wsl_install.txt"
$url = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$name = "$dirPATH\wsl_update_x64.msi"

try {
    # Enabling the Windows Subsystem for Linux;
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

    # Enabling Virtual Machine feature;
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

    # Downloading the Linux kernel update package;
    Invoke-RestMethod $url -Outfile $name

    # Executing the Linux kernel update package;
    Start-Process -FilePath $name -Wait
    # Deleting the Linux kernel update package;
    Remove-Item -Path $name

    # Setting WSL 2 as your default version;
    wsl --set-default-version 2

    Clear-host
    Write-Output "Made It"
    Restart-Computer -Confirm
} catch {
    Clear-host
    Clear-Content -Force -LiteralPath $logfile
    Write-Output "Something goes wrong! See log-wsl_install.txt"
    Out-File -Force -FilePath $logfile -InputObject $Error -Encoding utf8 -Width 128
}
