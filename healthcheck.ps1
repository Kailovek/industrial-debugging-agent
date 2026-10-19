param([int]$Port = 8102)
$Response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/v1/health" -TimeoutSec 5
$Response | ConvertTo-Json -Depth 5
if ($Response.status -ne "healthy") { throw "Agent API is not healthy." }
