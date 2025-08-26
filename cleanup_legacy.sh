#!/bin/bash

# Legacy Cleanup Script for AI Chatbot Project
# Bash version for Unix/Linux/macOS
# This script removes legacy microservices and files after FastAPI migration

set -e  # Exit on any error

# Default options
DRY_RUN=false
FORCE=false
HELP=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

if [ "$HELP" = true ]; then
    cat << 'EOF'
Legacy Cleanup Script for AI Chatbot Project

USAGE:
    ./cleanup_legacy.sh [OPTIONS]

OPTIONS:
    --dry-run     Show what would be deleted without actually deleting
    --force       Skip confirmation prompts
    --help, -h    Show this help message

EXAMPLES:
    ./cleanup_legacy.sh --dry-run        # Preview what will be deleted
    ./cleanup_legacy.sh                  # Interactive cleanup with confirmations
    ./cleanup_legacy.sh --force          # Cleanup without confirmations

EOF
    exit 0
fi

function print_color() {
    local message="$1"
    local color="$2"
    echo -e "${color}${message}${NC}"
}

function test_fastapi_backend() {
    print_color "🔍 Verifying FastAPI backend exists..." "$BLUE"
    
    if [ ! -d "fastapi-backend" ]; then
        print_color "❌ ERROR: fastapi-backend directory not found!" "$RED"
        print_color "   This script should only be run after successful FastAPI migration." "$RED"
        return 1
    fi
    
    local required_files=(
        "fastapi-backend/main.py"
        "fastapi-backend/services/crawler.py"
        "fastapi-backend/services/embedding.py"
        "fastapi-backend/services/parser.py"
        "fastapi-backend/services/rag.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_color "❌ ERROR: Required file missing: $file" "$RED"
            return 1
        fi
    done
    
    print_color "✅ FastAPI backend verification passed" "$GREEN"
    return 0
}

function get_directory_size() {
    local path="$1"
    if [ -d "$path" ]; then
        du -sm "$path" 2>/dev/null | cut -f1 || echo "0"
    else
        echo "0"
    fi
}

function remove_item_safely() {
    local path="$1"
    local description="$2"
    
    if [ ! -e "$path" ]; then
        print_color "⚠️  $description not found: $path" "$YELLOW"
        return
    fi
    
    local size=""
    if [ -d "$path" ]; then
        local size_mb=$(get_directory_size "$path")
        if [ "$size_mb" -gt 0 ]; then
            size=" (${size_mb}MB)"
        fi
    fi
    
    if [ "$DRY_RUN" = true ]; then
        print_color "🔍 Would remove: $description$size" "$BLUE"
        return
    fi
    
    if rm -rf "$path" 2>/dev/null; then
        print_color "✅ Removed: $description$size" "$GREEN"
    else
        print_color "❌ Failed to remove: $description" "$RED"
    fi
}

# Main execution
print_color "🧹 AI Chatbot Legacy Cleanup Script" "$BLUE"
print_color "====================================" "$BLUE"

if [ "$DRY_RUN" = true ]; then
    print_color "🔍 DRY RUN MODE - No files will be deleted" "$YELLOW"
fi

# Verify FastAPI backend exists
if ! test_fastapi_backend; then
    print_color "❌ Aborting cleanup due to missing FastAPI backend" "$RED"
    exit 1
fi

# Calculate total size before cleanup
print_color "\n📊 Calculating current disk usage..." "$BLUE"
total_size_before=0

legacy_dirs=("api" "crawler" "embedding_service" "parser" "rag" "vector_db")
for dir in "${legacy_dirs[@]}"; do
    size=$(get_directory_size "$dir")
    total_size_before=$((total_size_before + size))
done

print_color "💾 Legacy components using: ${total_size_before}MB" "$BLUE"

# Confirmation prompt
if [ "$DRY_RUN" = false ] && [ "$FORCE" = false ]; then
    print_color "\n⚠️  WARNING: This will permanently delete legacy components!" "$YELLOW"
    print_color "   Make sure you have backups if needed." "$YELLOW"
    echo -n -e "\nDo you want to continue? (y/N): "
    read -r confirmation
    if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
        print_color "❌ Cleanup cancelled by user" "$YELLOW"
        exit 0
    fi
fi

print_color "\n🗂️  Removing legacy service directories..." "$BLUE"

# Remove legacy service directories
declare -A legacy_directories=(
    ["api"]="Cloudflare Worker API directory"
    ["crawler"]="Legacy crawler service directory"
    ["embedding_service"]="Legacy embedding service directory"
    ["parser"]="Legacy parser service directory"
    ["rag"]="Legacy RAG service directory"
    ["vector_db"]="Local Qdrant Docker setup directory"
)

for path in "${!legacy_directories[@]}"; do
    remove_item_safely "$path" "${legacy_directories[$path]}"
done

print_color "\n📄 Removing legacy service files..." "$BLUE"

# Remove legacy service files
declare -A legacy_files=(
    ["crawler_service.py"]="Flask crawler service"
    ["embedding_service.py"]="Flask embedding service"
    ["parser_service.py"]="Flask parser service"
    ["rag_service.py"]="Flask RAG service"
    ["realtime_crawl_service.py"]="Flask realtime crawl service"
)

for path in "${!legacy_files[@]}"; do
    remove_item_safely "$path" "${legacy_files[$path]}"
done

print_color "\n🚀 Removing legacy startup scripts..." "$BLUE"

# Remove legacy startup/shutdown scripts
declare -A legacy_scripts=(
    ["start_all_services.ps1"]="PowerShell startup script"
    ["start_all_services.sh"]="Bash startup script"
    ["start_services_with_realtime.ps1"]="PowerShell with realtime"
    ["start_services.bat"]="Windows batch startup"
    ["start_services.ps1"]="PowerShell startup"
    ["start_services.sh"]="Bash startup script"
    ["stop_all_services.ps1"]="PowerShell stop script"
    ["stop_all_services.sh"]="Bash stop script"
)

for path in "${!legacy_scripts[@]}"; do
    remove_item_safely "$path" "${legacy_scripts[$path]}"
done

print_color "\n🧪 Removing legacy test files..." "$BLUE"

# Remove legacy test files
declare -A legacy_tests=(
    ["test_all_crawl_apis.py"]="Old crawl API tests"
    ["test_bot_creation.py"]="Old bot creation tests"
    ["test_chat.py"]="Old chat service tests"
    ["test_complete_rag_system.py"]="Old RAG system tests"
    ["test_crawl.py"]="Old crawler tests"
    ["test_crawler_service.py"]="Old crawler service tests"
    ["test_crawler_startup.py"]="Old crawler startup tests"
    ["test_dimensions.py"]="Old dimension tests"
    ["test_document_parsing.py"]="Old document parsing tests"
    ["test_rag_direct.py"]="Old direct RAG tests"
    ["test_realtime_crawl.py"]="Old realtime crawl tests"
)

for path in "${!legacy_tests[@]}"; do
    remove_item_safely "$path" "${legacy_tests[$path]}"
done

print_color "\n🔧 Removing legacy utility files..." "$BLUE"

# Remove legacy utility files
declare -A legacy_utils=(
    ["check_collection_content.py"]="Old collection checker"
    ["create_authenticated_bot.py"]="Old bot creation utility"
    ["create_test_bot.py"]="Old test bot utility"
    ["debug_rag_system.py"]="Old RAG debugging utility"
    ["recreate_collection.py"]="Old collection recreation utility"
    ["requirements.txt"]="Root requirements file (replaced by fastapi-backend/requirements.txt)"
)

for path in "${!legacy_utils[@]}"; do
    remove_item_safely "$path" "${legacy_utils[$path]}"
done

print_color "\n📚 Removing legacy documentation..." "$BLUE"

# Remove legacy documentation
declare -A legacy_docs=(
    ["REALTIME_CRAWL_README.md"]="Old realtime crawl documentation"
    ["realtime_crawl_test.html"]="Old realtime crawl test HTML"
)

for path in "${!legacy_docs[@]}"; do
    remove_item_safely "$path" "${legacy_docs[$path]}"
done

# Clean up empty logs directory if it exists and is empty
if [ -d "logs" ] && [ -z "$(ls -A logs)" ]; then
    remove_item_safely "logs" "Empty logs directory"
fi

print_color "\n✨ Cleanup Summary" "$BLUE"
print_color "==================" "$BLUE"

if [ "$DRY_RUN" = true ]; then
    print_color "🔍 DRY RUN COMPLETED - No files were actually deleted" "$YELLOW"
    print_color "💾 Estimated space savings: ${total_size_before}MB" "$BLUE"
else
    print_color "✅ Legacy cleanup completed successfully!" "$GREEN"
    print_color "💾 Disk space freed: ~${total_size_before}MB" "$GREEN"
fi

print_color "\n🎯 Next Steps:" "$BLUE"
print_color "1. Test the FastAPI backend: cd fastapi-backend && python main.py" "$BLUE"
print_color "2. Run tests: cd fastapi-backend && python -m pytest tests/" "$BLUE"
print_color "3. Start dashboard: cd dashboard && npm start" "$BLUE"

print_color "\n📖 For more information, see LEGACY_CLEANUP_GUIDE.md" "$BLUE"