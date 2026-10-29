$ErrorActionPreference = "Stop"

$Root = [System.IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$Sdk = $env:ANDROID_HOME
if (-not $Sdk) { $Sdk = $env:ANDROID_SDK_ROOT }
if (-not $Sdk) { $Sdk = Join-Path $env:LOCALAPPDATA "Android\Sdk" }
if (-not (Test-Path -LiteralPath $Sdk)) {
    throw "Android SDK not found. Set ANDROID_HOME or install Android SDK command-line tools."
}

$BuildToolsRoot = Join-Path $Sdk "build-tools"
$BuildTools = Get-ChildItem -LiteralPath $BuildToolsRoot -Directory |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $BuildTools) { throw "No Android build-tools found in $BuildToolsRoot." }

$PlatformsRoot = Join-Path $Sdk "platforms"
$Platform = Get-ChildItem -LiteralPath $PlatformsRoot -Directory |
    Sort-Object Name -Descending |
    Select-Object -First 1
if (-not $Platform) { throw "No Android platforms found in $PlatformsRoot." }

$Aapt2 = Join-Path $BuildTools.FullName "aapt2.exe"
$Zipalign = Join-Path $BuildTools.FullName "zipalign.exe"
$Apksigner = Join-Path $BuildTools.FullName "apksigner.bat"
$AndroidJar = Join-Path $Platform.FullName "android.jar"
$D8 = Join-Path $Sdk "cmdline-tools\latest\bin\d8.bat"

foreach ($Tool in @($Aapt2, $Zipalign, $Apksigner, $AndroidJar, $D8)) {
    if (-not (Test-Path -LiteralPath $Tool)) { throw "Required Android tool missing: $Tool" }
}

$JavaHome = $env:JAVA_HOME
if (-not $JavaHome) {
    $JavaCommand = Get-Command java -ErrorAction SilentlyContinue
    if (-not $JavaCommand) { throw "Java not found. Install JDK 17 or set JAVA_HOME." }
    $JavaHome = Split-Path -Parent (Split-Path -Parent $JavaCommand.Source)
}
$Javac = Join-Path $JavaHome "bin\javac.exe"
$Jar = Join-Path $JavaHome "bin\jar.exe"
$Keytool = Join-Path $JavaHome "bin\keytool.exe"
foreach ($Tool in @($Javac, $Jar, $Keytool)) {
    if (-not (Test-Path -LiteralPath $Tool)) { throw "Required JDK tool missing: $Tool" }
}

$Build = [System.IO.Path]::GetFullPath((Join-Path $Root "build"))
if ((Split-Path -Parent $Build) -ne $Root -or (Split-Path -Leaf $Build) -ne "build") {
    throw "Build output must be the android/build directory."
}
$Compiled = Join-Path $Build "compiled"
$Generated = Join-Path $Build "generated"
$Classes = Join-Path $Build "classes"
$Dex = Join-Path $Build "dex"
$UnsignedApk = Join-Path $Build "mathblitz-unsigned.apk"
$AlignedApk = Join-Path $Build "mathblitz-aligned.apk"
$SignedApk = Join-Path $Build "mathblitz-debug.apk"
$Keystore = Join-Path $Root "debug.keystore"
$PreviousKeystore = Join-Path $Build "debug.keystore"
if (-not (Test-Path -LiteralPath $Keystore) -and (Test-Path -LiteralPath $PreviousKeystore)) {
    Copy-Item -LiteralPath $PreviousKeystore -Destination $Keystore
}

if (Test-Path -LiteralPath $Build) { Remove-Item -LiteralPath $Build -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Compiled, $Generated, $Classes, $Dex | Out-Null

& $Aapt2 compile --dir (Join-Path $Root "app\src\main\res") -o $Compiled
if ($LASTEXITCODE -ne 0) { throw "aapt2 compile failed." }

$FlatFiles = Get-ChildItem -Path $Compiled -Filter *.flat | ForEach-Object FullName
if (-not $FlatFiles) { throw "No compiled Android resources found." }

& $Aapt2 link `
    -I $AndroidJar `
    --manifest (Join-Path $Root "app\src\main\AndroidManifest.xml") `
    --java $Generated `
    -o $UnsignedApk `
    @FlatFiles
if ($LASTEXITCODE -ne 0) { throw "aapt2 link failed." }

$SourceFiles = @()
$SourceFiles += Get-ChildItem -Path (Join-Path $Root "app\src\main\java") -Recurse -Filter *.java | ForEach-Object FullName
$SourceFiles += Get-ChildItem -Path $Generated -Recurse -Filter *.java | ForEach-Object FullName
if (-not $SourceFiles) { throw "No Java source files found." }

& $Javac -encoding UTF-8 -source 8 -target 8 -classpath $AndroidJar -d $Classes @SourceFiles
if ($LASTEXITCODE -ne 0) { throw "javac failed." }

$ClassFiles = Get-ChildItem -Path $Classes -Recurse -Filter *.class | ForEach-Object FullName
& $D8 --min-api 23 --lib $AndroidJar --output $Dex @ClassFiles
if ($LASTEXITCODE -ne 0) { throw "d8 failed." }

& $Jar uf $UnsignedApk -C $Dex classes.dex
if ($LASTEXITCODE -ne 0) { throw "Adding dex to APK failed." }

& $Zipalign -f 4 $UnsignedApk $AlignedApk
if ($LASTEXITCODE -ne 0) { throw "zipalign failed." }

if (-not (Test-Path -LiteralPath $Keystore)) {
    & $Keytool -genkeypair `
        -alias androiddebugkey `
        -keyalg RSA `
        -keysize 2048 `
        -validity 10000 `
        -keystore $Keystore `
        -storepass android `
        -keypass android `
        -dname "CN=Android Debug,O=MathBlitz,C=US" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "debug keystore generation failed." }
}

& $Apksigner sign `
    --ks $Keystore `
    --ks-pass pass:android `
    --key-pass pass:android `
    --out $SignedApk `
    $AlignedApk
if ($LASTEXITCODE -ne 0) { throw "APK signing failed." }

& $Apksigner verify $SignedApk
if ($LASTEXITCODE -ne 0) { throw "APK verification failed." }

Write-Output "Built $SignedApk"
