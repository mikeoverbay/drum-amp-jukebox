# Builds SONGIDX.TXT on the SD card for coffee_player.ino.
# Record: 64 bytes = 8.3 short name padded to 12 + '|' + display name padded to 50 + LF.
# Display name: from SONG_NAMES.txt (next to this script) if the song is listed there,
# else "Artist - Title" from the MP3 tags, else the long filename.
# Usage: powershell -ExecutionPolicy Bypass -File MakeSongIndex.ps1 [-Drive I:]
param([string]$Drive = 'I:')

# Display names that replace whatever the tags or filename say.
$Overrides = @{ 'HAUNTED1.MP3' = 'Scary Halloween sounds' }
# SONG_NAMES.txt lines: SHORTNAME|Artist: Song|note  ('#' starts a comment line).
$namesFile = Join-Path $PSScriptRoot 'SONG_NAMES.txt'
if (Test-Path $namesFile) {
  foreach ($line in Get-Content $namesFile) {
    if (-not $line -or $line.StartsWith('#')) { continue }
    $parts = $line -split '\|'
    if ($parts.Count -ge 2 -and $parts[1].Trim()) { $Overrides[$parts[0].Trim().ToUpper()] = $parts[1].Trim() }
  }
}

$NameWidth = 12
$TitleWidth = 50
$root = $Drive.TrimEnd('\') + '\'
if (-not (Test-Path $root)) { Write-Error "Drive $root not found. Is the SD card in?"; exit 1 }
$ffprobe = (Get-Command ffprobe -ErrorAction SilentlyContinue).Source
if (-not $ffprobe) {
  $ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
  if ($ffmpeg) { $ffprobe = Join-Path (Split-Path $ffmpeg) 'ffprobe.exe' }
}
if (-not $ffprobe -or -not (Test-Path $ffprobe)) { Write-Warning 'ffprobe not found; using filenames only.' }
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$fso = New-Object -ComObject Scripting.FileSystemObject

# The display font is ASCII only: strip accents, drop anything else, keep '|' out.
function Clean([string]$s) {
  $d = $s.Normalize([Text.NormalizationForm]::FormD)
  $b = New-Object Text.StringBuilder
  foreach ($c in $d.ToCharArray()) {
    if ([int]$c -ge 32 -and [int]$c -le 126 -and $c -ne '|') { [void]$b.Append($c) }
  }
  ($b.ToString() -replace '\s+', ' ').Trim()
}

$records = @()
$skipped = 0
foreach ($f in Get-ChildItem $root -File | Where-Object { $_.Extension -ieq '.mp3' }) {
  $short = $fso.GetFile($f.FullName).ShortName.ToUpper()
  if ($short.Length -gt $NameWidth -or $short -notmatch '^[^.]{1,8}\.MP3$') {
    Write-Warning "No usable 8.3 name, skipped: $($f.Name)"; $skipped++; continue
  }
  $title = ''
  if ($ffprobe) {
    $json = & $ffprobe -v error -show_entries format_tags=artist,title -of json $f.FullName | Out-String
    $tags = (ConvertFrom-Json $json).format.tags
    if ($tags) {
      $artist = Clean ([string]$tags.artist)
      $song = Clean ([string]$tags.title)
      if ($artist -and $song) { $title = "$artist - $song" } elseif ($song) { $title = $song }
    }
  }
  if (-not $title) { $title = Clean $f.BaseName }
  if ($Overrides.ContainsKey($short)) { $title = $Overrides[$short] }
  if ($title.Length -gt $TitleWidth) { $title = $title.Substring(0, $TitleWidth).TrimEnd() }
  $records += [pscustomobject]@{ Short = $short; Title = $title }
}

$sb = New-Object Text.StringBuilder
foreach ($r in $records | Sort-Object Title) {
  [void]$sb.Append($r.Short.PadRight($NameWidth)).Append('|').Append($r.Title.PadRight($TitleWidth)).Append("`n")
}
[IO.File]::WriteAllBytes((Join-Path $root 'SONGIDX.TXT'), [Text.Encoding]::ASCII.GetBytes($sb.ToString()))
"Wrote $($records.Count) records to ${root}SONGIDX.TXT ($skipped skipped)."
