Add-Type -AssemblyName System.Drawing

$cols = 9
$rows = 7
$sq = 200
$m = 200
$w = $cols * $sq + 2 * $m
$h = $rows * $sq + 2 * $m

$bmp = New-Object System.Drawing.Bitmap($w, $h)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$white = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
$black = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::Black)

$g.FillRectangle($white, 0, 0, $w, $h)
for ($r = 0; $r -lt $rows; $r++) {
    for ($c = 0; $c -lt $cols; $c++) {
        if (($r + $c) % 2 -eq 0) {
            $x = $m + $c * $sq
            $y = $m + $r * $sq
            $g.FillRectangle($black, $x, $y, $sq, $sq)
        }
    }
}

$out = "e:\ros2_working_place\checkerboard_8x6_25mm.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()

Write-Output "Generated: $out"
Write-Output "Size: ${w}x${h} px"
Write-Output "Pattern: ${cols}x${rows} squares = 8x6 inner corners"
Write-Output "Square: 25mm"
Write-Output "Print: A4 landscape, 100% scale, no fit-to-page"
