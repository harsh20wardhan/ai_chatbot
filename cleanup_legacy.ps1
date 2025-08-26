# Legacy Cleanup Script for AI Chatbot Project
# PowerShell version for Windows
# This script removes legacy microservices and files after FastAPI migration

param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Legacy Cleanup Script for AI Chatbot Project

USAGE:
    .\cleanup_legacy.ps1 [OPTIONS]

OPTIONS:
    -DryRun     Show what would be deleted without actually deleting
    -Force      Skip confirmation prompts
    -Help       Show this help message

EXAMPLES:
    .\cleanup_legacy.ps1 -DryRun          # Preview what will be deleted
    .\cleanup_legacy.ps1                  # Interactive cleanup with confirmations
    .\cleanup_legacy.ps1 -Force           # Cleanup without confirmations

"@
    exit 0
}

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-ColorOutput {
    param($Message, $Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-FastAPIBackend {
    Write-ColorOutput "🔍 Verifying FastAPI backend exists..." $Blue
    
    if (-not (Test-Path "fastapi-backend")) {
        Write-ColorOutput "❌ ERROR: fastapi-backend directory not found!" $Red
        Write-ColorOutput "   This script should only be run after successful FastAPI migration." $Red
        return $false
    }
    
    $requiredFiles = @(
        "fastapi-backend/main.py",
        "fastapi-backend/services/crawler.py",
        "fastapi-backend/services/embedding.py",
        "fastapi-backend/services/parser.py",
        "fastapi-backend/services/rag.py"
    )
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Write-ColorOutput "❌ ERROR: Required file missing: $file" $Red
            return $false
        }
    }
    
    Write-ColorOutput "✅ FastAPI backend verification passed" $Green
    return $true
}

function Get-DirectorySize {
    param($Path)
    if (Test-Path $Path) {
        $size = (Get-ChildItem -Path $Path -Recurse -File | Measure-Object -Property Length -Sum).Sum
        return [math]::Round($size / 1MB, 2)
    }
    return 0
}

function Remove-ItemSafely {
    param($Path, $Description)
    
    if (-not (Test-Path $Path)) {
        Write-ColorOutput "⚠️  $Description not found: $Path" $Yellow
        return
    }
    
    $size = Get-DirectorySize $Path
    $sizeText = if ($size -gt 0) { " (${size}MB)" } else { "" }
    
    if ($DryRun) {
        Write-ColorOutput "🔍 Would remove: $Description$sizeText" $Blue
        return
    }
    
    try {
        if (Test-Path $Path -PathType Container) {
            Remove-Item -Path $Path -Recurse -Force
        } else {
            Remove-Item -Path $Path -Force
        }
        Write-ColorOutput "✅ Removed: $Description$sizeText" $Green
    } catch {
        Write-ColorOutput "❌ Failed to remove: $Description - $($_.Exception.Message)" $Red
    }
}

# Main execution
Write-ColorOutput "🧹 AI Chatbot Legacy Cleanup Script" $Blue
Write-ColorOutput "====================================" $Blue

if ($DryRun) {
    Write-ColorOutput "🔍 DRY RUN MODE - No files will be deleted" $Yellow
}

# Verify FastAPI backend exists
if (-not (Test-FastAPIBackend)) {
    Write-ColorOutput "❌ Aborting cleanup due to missing FastAPI backend" $Red
    exit 1
}

# Calculate total size before cleanup
Write-ColorOutput "`n📊 Calculating current disk usage..." $Blue
$totalSizeBefore = 0

$legacyDirs = @("api", "crawler", "embedding_service", "parser", "rag", "vector_db")
foreach ($dir in $legacyDirs) {
    $totalSizeBefore += Get-DirectorySize $dir
}

Write-ColorOutput "💾 Legacy components using: ${totalSizeBefore}MB" $Blue

# Confirmation prompt
if (-not $DryRun -and -not $Force) {
    Write-ColorOutput "`n⚠️  WARNING: This will permanently delete legacy components!" $Yellow
    Write-ColorOutput "   Make sure you have backups if needed." $Yellow
    $confirmation = Read-Host "`nDo you want to continue? (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-ColorOutput "❌ Cleanup cancelled by user" $Yellow
        exit 0
    }
}

Write-ColorOutput "`n🗂️  Removing legacy service directories..." $Blue

# Remove legacy service directories
$legacyDirectories = @(
    @{Path="api"; Description="Cloudflare Worker API directory"},
    @{Path="crawler"; Description="Legacy crawler service directory"},
    @{Path="embedding_service"; Description="Legacy embedding service directory"},
    @{Path="parser"; Description="Legacy parser service directory"},
    @{Path="rag"; Description="Legacy RAG service directory"},
    @{Path="vector_db"; Description="Local Qdrant Docker setup directory"}
)

foreach ($item in $legacyDirectories) {
    Remove-ItemSafely $item.Path $item.Description
}

Write-ColorOutput "`n📄 Removing legacy service files..." $Blue

# Remove legacy service files
$legacyFiles = @(
    @{Path="crawler_service.py"; Description="Flask crawler service"},
    @{Path="embedding_service.py"; Description="Flask embedding service"},
    @{Path="parser_service.py"; Description="Flask parser service"},
    @{Path="rag_service.py"; Description="Flask RAG service"},
    @{Path="realtime_crawl_service.py"; Description="Flask realtime crawl service"}
)

foreach ($item in $legacyFiles) {
    Remove-ItemSafely $item.Path $item.Description
}

Write-ColorOutput "`n🚀 Removing legacy startup scripts..." $Blue

# Remove legacy startup/shutdown scripts
$legacyScripts = @(
    @{Path="start_all_services.ps1"; Description="PowerShell startup script"},
    @{Path="start_all_services.sh"; Description="Bash startup script"},
    @{Path="start_services_with_realtime.ps1"; Description="PowerShell with realtime"},
    @{Path="start_services.bat"; Description="Windows batch startup"},
    @{Path="start_services.ps1"; Description="PowerShell startup"},
    @{Path="start_services.sh"; Description="Bash startup script"},
    @{Path="stop_all_services.ps1"; Description="PowerShell stop script"},
    @{Path="stop_all_services.sh"; Description="Bash stop script"}
)

foreach ($item in $legacyScripts) {
    Remove-ItemSafely $item.Path $item.Description
}

Write-ColorOutput "`n🧪 Removing legacy test files..." $Blue

# Remove legacy test files
$legacyTests = @(
    @{Path="test_all_crawl_apis.py"; Description="Old crawl API tests"},
    @{Path="test_bot_creation.py"; Description="Old bot creation tests"},
    @{Path="test_chat.py"; Description="Old chat service tests"},
    @{Path="test_complete_rag_system.py"; Description="Old RAG system tests"},
    @{Path="test_crawl.py"; Description="Old crawler tests"},
    @{Path="test_crawler_service.py"; Description="Old crawler service tests"},
    @{Path="test_crawler_startup.py"; Description="Old crawler startup tests"},
    @{Path="test_dimensions.py"; Description="Old dimension tests"},
    @{Path="test_document_parsing.py"; Description="Old document parsing tests"},
    @{Path="test_rag_direct.py"; Description="Old direct RAG tests"},
    @{Path="test_realtime_crawl.py"; Description="Old realtime crawl tests"}
)

foreach ($item in $legacyTests) {
    Remove-ItemSafely $item.Path $item.Description
}

Write-ColorOutput "`n🔧 Removing legacy utility files..." $Blue

# Remove legacy utility files
$legacyUtils = @(
    @{Path="check_collection_content.py"; Description="Old collection checker"},
    @{Path="create_authenticated_bot.py"; Description="Old bot creation utility"},
    @{Path="create_test_bot.py"; Description="Old test bot utility"},
    @{Path="debug_rag_system.py"; Description="Old RAG debugging utility"},
    @{Path="recreate_collection.py"; Description="Old collection recreation utility"},
    @{Path="requirements.txt"; Description="Root requirements file (replaced by fastapi-backend/requirements.txt)"}
)

foreach ($item in $legacyUtils) {
    Remove-ItemSafely $item.Path $item.Description
}

Write-ColorOutput "`n📚 Removing legacy documentation..." $Blue

# Remove legacy documentation
$legacyDocs = @(
    @{Path="REALTIME_CRAWL_README.md"; Description="Old realtime crawl documentation"},
    @{Path="realtime_crawl_test.html"; Description="Old realtime crawl test HTML"}
)

foreach ($item in $legacyDocs) {
    Remove-ItemSafely $item.Path $item.Description
}

# Clean up empty logs directory if it exists and is empty
if (Test-Path "logs" -PathType Container) {
    $logFiles = Get-ChildItem -Path "logs" -File
    if ($logFiles.Count -eq 0) {
        Remove-ItemSafely "logs" "Empty logs directory"
    }
}

Write-ColorOutput "`n✨ Cleanup Summary" $Blue
Write-ColorOutput "==================" $Blue

if ($DryRun) {
    Write-ColorOutput "🔍 DRY RUN COMPLETED - No files were actually deleted" $Yellow
    Write-ColorOutput "💾 Estimated space savings: ${totalSizeBefore}MB" $Blue
} else {
    Write-ColorOutput "✅ Legacy cleanup completed successfully!" $Green
    Write-ColorOutput "💾 Disk space freed: ~${totalSizeBefore}MB" $Green
}

Write-ColorOutput "`n🎯 Next Steps:" $Blue
Write-ColorOutput "1. Test the FastAPI backend: cd fastapi-backend && python main.py" $Blue
Write-ColorOutput "2. Run tests: cd fastapi-backend && python -m pytest tests/" $Blue
Write-ColorOutput "3. Start dashboard: cd dashboard && npm start" $Blue

Write-ColorOutput "`n📖 For more information, see LEGACY_CLEANUP_GUIDE.md" $Blue