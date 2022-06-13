<#
    .Synopsis

    .Description

    .Parameter url
        URL of the download link of the program you want to install;

    .Parameter name
        Given name to the executable file which are downloaded from the url, is need to give the extension of the file (i.e.: filename.exe, filename.msi);

    .Example
            Download-Install "www.foo.com/example.exe" "example.exe"

    .Notes
            Author:     Gabriel Marino;
            Email:      gcmarino404@gmail.com
#>

function CLS {
    #   Searching for all .txt, .exe and .msi files and removing them in the path where PS1 is being executed;
    #   asterisk denote which get-childitem have to search only where the PS1 is being executed;
    Get-ChildItem * -Include *.txt, *.exe, *.msi -Recurse | Remove-Item
}

function Execute-All {
    #   Searching for all .exe and .msi files and executing them in the path where PS1 is being executed;
    Get-ChildItem * -Include *.exe, *.msi -Recurse | Start-Process -ArgumentList -NoProfile -Wait
    CLS
}

function Download-Install {

    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]
        $url,
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]
        $name
    )

#   Directory path where Batch is being executed;
    $path = Get-Location
    $logfile = "$path\log.txt"

    try {
#       Invoke-RestMethod download the file of the url give and wait to download conclude;
        Invoke-RestMethod "$url" -Outfile "$path\$name"
        Start-Process -ArgumentList -NoProfile -File "$path\$name" -Wait
        Remove-Item -Force -Path $path\$name
        Out-file -Force -FilePath $logfile "Nothing went wrong!"
    } catch {
#       Print in the terminal the quoted message;
        Write-Output "S$path\omething goes wrong! See Log.txt"
#       Write in the Log.txt what went wrong;
        Out-File -Force -FilePath $logfile -InputObject $Error -Encoding utf8 -Width 128
    }
#   Clean the terminal;
    Clear-Host
#   Warns which the PS1 completed and succed the execution;
    Write-Output "Made It"
}

Export-ModuleMember -Function * -Alias *