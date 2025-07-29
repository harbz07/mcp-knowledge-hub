# Script to POST sanctuary payload files to MCP Knowledge Hub
$baseUrl = "https://knowledge-hub-mcp.harveytagalicud7.workers.dev"

# Function to POST content to knowledge hub
function Post-ToKnowledgeHub {
    param(
        [string]$Content,
        [string]$Tags,
        [string]$Source,
        [string]$Filename
    )
    
    $requestBody = @{
        jsonrpc = "2.0"
        id = (Get-Random)
        method = "tools/call"
        params = @{
            name = "store_context"
            arguments = @{
                content = $Content
                tags = $Tags -split ","
                source = $Source
                metadata = @{
                    filename = $Filename
                    category = "sanctuary_payload"
                }
            }
        }
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-WebRequest -Uri $baseUrl -Method POST -Headers @{"Content-Type"="application/json"} -Body $requestBody
        Write-Host " Successfully posted: $Filename" -ForegroundColor Green
        return $response.Content
    }
    catch {
        Write-Host " Failed to post: $Filename" -ForegroundColor Red
        Write-Host $_.Exception.Message
        return $null
    }
}

Write-Host " Starting to POST sanctuary payload files to Knowledge Hub..." -ForegroundColor Cyan

# 1. POST forms_knowledge_index.json
Write-Host " Posting forms knowledge index..." -ForegroundColor Yellow
$formsContent = Get-Content "sanctuary_payload\forms_knowledge_index.json" -Raw
Post-ToKnowledgeHub -Content $formsContent -Tags "sanctuary,forms,persona_modes,harvey" -Source "sanctuary-archive" -Filename "forms_knowledge_index.json"

# 2. POST sanctuary_archive_spec.yaml
Write-Host " Posting sanctuary archive spec..." -ForegroundColor Yellow
$specContent = Get-Content "sanctuary_payload\sanctuary_archive_spec.yaml" -Raw
Post-ToKnowledgeHub -Content $specContent -Tags "sanctuary,specification,yaml,archive" -Source "sanctuary-archive" -Filename "sanctuary_archive_spec.yaml"

# 3. POST sanctuary_vector_entity_ledger.sql
Write-Host " Posting vector entity ledger..." -ForegroundColor Yellow
$ledgerContent = Get-Content "sanctuary_payload\sanctuary_vector_entity_ledger.sql" -Raw
Post-ToKnowledgeHub -Content $ledgerContent -Tags "sanctuary,sql,vector,entity,ledger" -Source "sanctuary-archive" -Filename "sanctuary_vector_entity_ledger.sql"

# 4. POST save_log.yaml
Write-Host " Posting save log..." -ForegroundColor Yellow
$saveLogContent = Get-Content "sanctuary_payload\save_log.yaml" -Raw
Post-ToKnowledgeHub -Content $saveLogContent -Tags "sanctuary,log,yaml" -Source "sanctuary-archive" -Filename "save_log.yaml"

# 5. POST MCP Bridge files
Write-Host " Posting MCP Bridge files..." -ForegroundColor Yellow

# db.py
$dbContent = Get-Content "sanctuary_payload\sanctuary_mcp_bridge\sanctuary_mcp_bridge\db.py" -Raw
Post-ToKnowledgeHub -Content $dbContent -Tags "sanctuary,mcp,bridge,python,database" -Source "sanctuary-archive" -Filename "db.py"

# patterns.py
$patternsContent = Get-Content "sanctuary_payload\sanctuary_mcp_bridge\sanctuary_mcp_bridge\patterns.py" -Raw
Post-ToKnowledgeHub -Content $patternsContent -Tags "sanctuary,mcp,bridge,python,patterns" -Source "sanctuary-archive" -Filename "patterns.py"

# schemas.py
$schemasContent = Get-Content "sanctuary_payload\sanctuary_mcp_bridge\sanctuary_mcp_bridge\schemas.py" -Raw
Post-ToKnowledgeHub -Content $schemasContent -Tags "sanctuary,mcp,bridge,python,schemas" -Source "sanctuary-archive" -Filename "schemas.py"

# server.py
$serverContent = Get-Content "sanctuary_payload\sanctuary_mcp_bridge\sanctuary_mcp_bridge\server.py" -Raw
Post-ToKnowledgeHub -Content $serverContent -Tags "sanctuary,mcp,bridge,python,server" -Source "sanctuary-archive" -Filename "server.py"

# __init__.py
$initContent = Get-Content "sanctuary_payload\sanctuary_mcp_bridge\sanctuary_mcp_bridge\__init__.py" -Raw
Post-ToKnowledgeHub -Content $initContent -Tags "sanctuary,mcp,bridge,python,init" -Source "sanctuary-archive" -Filename "__init__.py"

Write-Host " Finished posting sanctuary payload files to Knowledge Hub!" -ForegroundColor Green
