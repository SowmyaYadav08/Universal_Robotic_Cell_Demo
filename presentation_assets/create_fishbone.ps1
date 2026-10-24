Add-Type -AssemblyName System.Drawing
$assetRoot = $PSScriptRoot
$svgPath = Join-Path $assetRoot 'light_localizer_fishbone.svg'
$pngPath = Join-Path $assetRoot 'light_localizer_fishbone.png'
$svgParts = [System.Collections.Generic.List[string]]::new()
$svgParts.Add('<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080"><title>Light Localizer fishbone analysis</title><desc>Potential causes of plate loss and process interruption. All branches are investigation hypotheses. Sensing and recovery branches describe detection and response gaps, not confirmed physical causes of the drop.</desc>')
$bitmap = [System.Drawing.Bitmap]::new(3840,2160)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.ScaleTransform(2,2)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$graphics.Clear([System.Drawing.Color]::White)

function Diagram-Color($hex) { [System.Drawing.ColorTranslator]::FromHtml($hex) }
function Diagram-Line($x1,$y1,$x2,$y2,$color,$width=2.5) {
    $pen = [System.Drawing.Pen]::new((Diagram-Color $color),[single]$width)
    $graphics.DrawLine($pen,[single]$x1,[single]$y1,[single]$x2,[single]$y2)
    $pen.Dispose()
    $svgParts.Add("<line x1='$x1' y1='$y1' x2='$x2' y2='$y2' stroke='$color' stroke-width='$width' stroke-linecap='round'/>")
}
function Diagram-Rect($x,$y,$w,$h,$color) {
    $brush = [System.Drawing.SolidBrush]::new((Diagram-Color $color))
    $graphics.FillRectangle($brush,[single]$x,[single]$y,[single]$w,[single]$h)
    $brush.Dispose()
    $svgParts.Add("<rect x='$x' y='$y' width='$w' height='$h' fill='$color'/>")
}
function Diagram-Text($text,$x,$y,$size,$color,$bold=$false) {
    $style = if ($bold) {[System.Drawing.FontStyle]::Bold} else {[System.Drawing.FontStyle]::Regular}
    $font = [System.Drawing.Font]::new('Segoe UI',[single]$size,$style,[System.Drawing.GraphicsUnit]::Pixel)
    $brush = [System.Drawing.SolidBrush]::new((Diagram-Color $color))
    $graphics.DrawString($text,$font,$brush,[single]$x,[single]$y)
    $escaped = [System.Security.SecurityElement]::Escape($text)
    $weight = if ($bold) {'700'} else {'400'}
    $baseline = $y + $size
    $svgParts.Add("<text x='$x' y='$baseline' font-family='Segoe UI,Arial,sans-serif' font-size='$size' font-weight='$weight' fill='$color'>$escaped</text>")
    $measured = $graphics.MeasureString($text,$font).Width
    $font.Dispose(); $brush.Dispose()
    return $measured
}

$navy = '#173D53'
$teal = '#087F8C'
$amber = '#A46B14'
$purple = '#75549A'
$ink = '#334E61'
$muted = '#627889'

Diagram-Rect 80 69 8 74 $teal
$null = Diagram-Text 'LIGHT LOCALIZER' 110 65 22 $teal $true
$null = Diagram-Text 'Plate Loss & Process Interruption' 106 103 44 $navy $true
$null = Diagram-Text 'Potential causes and process gaps | To be verified' 110 166 26 $muted
Diagram-Line 110 216 1810 216 '#DCE7EC' 1.5

# Shared effect spine and arrowhead.
Diagram-Line 115 550 1528 550 $navy 5
Diagram-Line 1506 535 1528 550 $navy 4
Diagram-Line 1506 565 1528 550 $navy 4
Diagram-Rect 1535 437 300 224 $navy
$null = Diagram-Text 'OBSERVED EFFECT' 1557 457 18 '#9DD9DE' $true
$null = Diagram-Text 'Plate lost' 1557 499 32 '#FFFFFF' $true
$null = Diagram-Text 'during transport' 1557 540 28 '#FFFFFF' $true
Diagram-Line 1558 588 1810 588 '#648494' 1
$null = Diagram-Text 'Assembly interrupted' 1557 610 21 '#E1ECF2'

$branches = @(
    @{ X=110; Joint=470; Top=$true; Color=$teal; Title='GRIPPER'; Causes=@('Low holding force') },
    @{ X=510; Joint=870; Top=$true; Color=$teal; Title='CONTROL'; Causes=@('Release at wrong time') },
    @{ X=910; Joint=1270; Top=$true; Color=$teal; Title='MOTION'; Causes=@('Excessive acceleration') },
    @{ X=110; Joint=470; Top=$false; Color=$teal; Title='CONTACT'; Causes=@('Low grip friction') },
    @{ X=510; Joint=870; Top=$false; Color=$amber; Title='SENSING'; Causes=@('Missing grip feedback') },
    @{ X=910; Joint=1270; Top=$false; Color=$purple; Title='RECOVERY'; Causes=@('No automatic retry') }
)
foreach ($branch in $branches) {
    $endX = $branch.Joint - 100
    $endY = if($branch.Top){355}else{755}
    Diagram-Line $branch.Joint 550 $endX $endY $branch.Color 3
    $headingY = if($branch.Top){300}else{800}
    Diagram-Rect $branch.X $headingY 6 34 $branch.Color
    $null = Diagram-Text $branch.Title ($branch.X+16) ($headingY-3) 29 $branch.Color $true
    $rows = if($branch.Top){@(412)}else{@(658)}
    for($i=0;$i -lt $branch.Causes.Count;$i++) {
        $baselineY = $rows[$i]+24
        $textWidth = Diagram-Text $branch.Causes[$i] $branch.X $rows[$i] 26 $ink
        $intersectX = $branch.Joint + ($endX-$branch.Joint)*(($baselineY-550)/($endY-550))
        $twigStart = $branch.X+$textWidth+8
        if($twigStart -gt $intersectX-12){$twigStart=$intersectX-12}
        Diagram-Line $twigStart $baselineY $intersectX $baselineY $branch.Color 1.6
    }
}

Diagram-Line 110 938 1810 938 '#DCE7EC' 1.5
Diagram-Rect 111 963 14 14 $teal
$null = Diagram-Text 'Potential loss causes' 138 956 20 $ink
Diagram-Rect 440 963 14 14 $amber
$null = Diagram-Text 'Detection gap' 467 956 20 $ink
Diagram-Rect 705 963 14 14 $purple
$null = Diagram-Text 'Recovery gap' 732 956 20 $ink
$null = Diagram-Text 'Observed: plate drop and assembly interruption. Physical root cause remains unconfirmed.' 110 1004 23 $muted
$svgParts.Add('</svg>')
[System.IO.File]::WriteAllText($svgPath,($svgParts -join "`n"),[System.Text.UTF8Encoding]::new($false))
$bitmap.Save($pngPath,[System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose(); $bitmap.Dispose()
Write-Output "Created SVG: $svgPath"
Write-Output "Created PNG: $pngPath"
