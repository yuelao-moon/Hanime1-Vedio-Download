param(
    [string]$AppHome = "",
    [int]$Port = 58080
)

$ErrorActionPreference = "Stop"
python -m pip install -r python_backend/requirements.txt
$argsList = @("python_backend/run.py", "--port", "$Port")
if ($AppHome) {
    $argsList += @("--app-home", $AppHome)
}
python @argsList
