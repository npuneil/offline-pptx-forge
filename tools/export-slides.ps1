param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$Width = 1600
)
$ErrorActionPreference = 'Stop'
$Pptx = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path
Get-ChildItem $OutDir -Filter 'slide*.png' -ErrorAction SilentlyContinue | Remove-Item -Force
$wasRunning = [bool](Get-Process POWERPNT -ErrorAction SilentlyContinue)
$app = New-Object -ComObject PowerPoint.Application
try {
    # ReadOnly, Untitled=false, WithWindow=false
    $pres = $app.Presentations.Open($Pptx, -1, 0, 0)
    $i = 1
    foreach ($s in $pres.Slides) {
        $s.Export((Join-Path $OutDir ('slide{0:D2}.png' -f $i)), 'PNG', $Width, [int]($Width * 9 / 16))
        $i++
    }
    $pres.Close()
}
finally {
    if (-not $wasRunning) { $app.Quit() }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
Write-Output "exported $($i - 1)"
