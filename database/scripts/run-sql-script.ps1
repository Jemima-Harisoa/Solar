param(
    [Parameter(Mandatory = $true)]
    [string]$SqlFile,

    [string]$ContainerName = "solar-sqlserver",
    [string]$Database = "master",
    [string]$SqlUser = "sa",
    [System.Management.Automation.PSCredential]$Credential
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker n'est pas disponible dans ce terminal."
}

if (-not (Test-Path -Path $SqlFile)) {
    throw "Le fichier SQL est introuvable: $SqlFile"
}

$sqlPassword = $null
if ($null -ne $Credential) {
    $SqlUser = $Credential.UserName
    $sqlPassword = $Credential.GetNetworkCredential().Password
} else {
    $sqlPassword = $env:SA_PASSWORD
}

if ([string]::IsNullOrWhiteSpace($sqlPassword)) {
    throw "Mot de passe SQL manquant. Passe -Credential (Get-Credential) ou definis SA_PASSWORD."
}

# Convertit le chemin en absolu pour eviter les problemes de contexte.
$absoluteSqlFile = (Resolve-Path -Path $SqlFile).Path
$leafName = Split-Path -Path $absoluteSqlFile -Leaf
$containerSqlPath = "/tmp/$leafName"

$containerId = docker ps --filter "name=^/$ContainerName$" --format "{{.ID}}"
if ([string]::IsNullOrWhiteSpace($containerId)) {
    throw "Conteneur introuvable ou arrete: $ContainerName"
}

Write-Host "Copie du script SQL vers le conteneur..."
docker cp "$absoluteSqlFile" "$ContainerName`:$containerSqlPath" | Out-Null

Write-Host "Execution du script SQL sur la base '$Database'..."
docker exec "$ContainerName" /opt/mssql-tools18/bin/sqlcmd -S localhost -U "$SqlUser" -P "$sqlPassword" -C -b -d "$Database" -i "$containerSqlPath"

Write-Host "Suppression du fichier temporaire..."
docker exec "$ContainerName" sh -lc "rm -f '$containerSqlPath' 2>/dev/null || true" | Out-Null

Write-Host "Execution terminee avec succes."
