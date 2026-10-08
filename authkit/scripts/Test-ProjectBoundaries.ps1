[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$rootPrefix = $projectRoot.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar

function Assert-LocalPath([string] $baseDirectory, [string] $relativePath) {
    # Explicit source/build paths must be literal so the check cannot silently
    # approve an unevaluated MSBuild property, wildcard or item expression.
    if ($relativePath -match '[\$@*?;]') {
        throw "Non-literal source/build path requires review: $relativePath"
    }
    $resolved = [IO.Path]::GetFullPath((Join-Path $baseDirectory $relativePath))
    if (-not $resolved.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes project root: $relativePath"
    }
    if (-not (Test-Path -LiteralPath $resolved)) {
        throw "Referenced file does not exist: $relativePath"
    }
    $cursor = Get-Item -LiteralPath $resolved
    while ($cursor.FullName -ne $projectRoot) {
        if ($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Source/build reference traverses a link: $relativePath"
        }
        $cursor = Get-Item -LiteralPath (Split-Path $cursor.FullName -Parent)
    }
    return $resolved
}

$projects = @(Get-ChildItem -LiteralPath $projectRoot -Recurse -Filter '*.csproj' |
    Where-Object { $_.FullName -notmatch '[\\/](bin|obj)[\\/]' })
foreach ($project in $projects) {
    [xml] $xml = Get-Content -LiteralPath $project.FullName -Raw
    foreach ($node in $xml.SelectNodes('//ProjectReference | //Compile | //Content | //None | //EmbeddedResource | //Import')) {
        if ($node.SelectSingleNode('Link') -or $node.HasAttribute('Link')) {
            throw "Linked source is forbidden: $($project.FullName)"
        }
        foreach ($attribute in @('Include', 'Update', 'Project')) {
            if ($node.HasAttribute($attribute)) {
                $null = Assert-LocalPath $project.DirectoryName $node.GetAttribute($attribute)
            }
        }
    }
    foreach ($hintPath in $xml.SelectNodes('//Reference/HintPath')) {
        $null = Assert-LocalPath $project.DirectoryName $hintPath.InnerText
    }
}

$solution = Join-Path $projectRoot 'AuthKit.sln'
foreach ($line in Get-Content -LiteralPath $solution) {
    if ($line -match '^Project\("[^\"]+"\) = "[^\"]+", "([^\"]+\.csproj)",') {
        $null = Assert-LocalPath $projectRoot $Matches[1]
    }
}
Write-Output "Project boundaries passed: $($projects.Count) projects, references contained in project root."
