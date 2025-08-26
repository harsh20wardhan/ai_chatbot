#!/usr/bin/env python3
"""
Dashboard API Update Script

This script helps update the dashboard API calls to match the FastAPI backend routes.
It can be used to automatically update the dashboard/src/services/api.js file.
"""

import os
import re
from pathlib import Path

def update_dashboard_api():
    """Update the dashboard API service file to match FastAPI backend routes"""
    
    dashboard_api_file = Path("../dashboard/src/services/api.js")
    
    if not dashboard_api_file.exists():
        print(f"❌ Dashboard API file not found: {dashboard_api_file}")
        print("Please ensure the dashboard directory is at the same level as fastapi-backend")
        return False
    
    print("🔄 Updating dashboard API calls to match FastAPI backend...")
    
    # Read the current file
    with open(dashboard_api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Store original content for backup
    backup_file = dashboard_api_file.with_suffix('.js.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📁 Created backup: {backup_file}")
    
    # Apply updates
    updates_made = []
    
    # 1. Update base URL
    old_base_url = "baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8787/api'"
    new_base_url = "baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api'"
    if old_base_url in content:
        content = content.replace(old_base_url, new_base_url)
        updates_made.append("✅ Updated base URL from port 8787 to 8000")
    
    # 2. Update document upload route
    old_upload = "const response = await api.post('/documents/upload', formData"
    new_upload = "const response = await api.post('/documents', formData"
    if old_upload in content:
        content = content.replace(old_upload, new_upload)
        updates_made.append("✅ Updated document upload route")
    
    # 3. Update crawl routes
    crawl_updates = [
        ("'/crawl/website'", "'/crawl'"),
        ("'/crawl/status/${jobId}'", "'/crawl/${jobId}'"),
        ("'/crawl/jobs?botId=${botId}'", "'/crawl?botId=${botId}'"),
        ("'/realtime-crawl/start'", "'/crawl/realtime'"),
        ("'/realtime-crawl/status/${jobId}'", "'/crawl/realtime/${jobId}'"),
    ]
    
    for old_route, new_route in crawl_updates:
        if old_route in content:
            content = content.replace(old_route, new_route)
            updates_made.append(f"✅ Updated crawl route: {old_route} → {new_route}")
    
    # 4. Update widget config method
    old_widget = "const response = await api.post(`/widget/${botId}/config`, configData);"
    new_widget = "const response = await api.put(`/widget/${botId}/config`, configData);"
    if old_widget in content:
        content = content.replace(old_widget, new_widget)
        updates_made.append("✅ Updated widget config method from POST to PUT")
    
    # 5. Update field names in crawl requests
    field_updates = [
        ("botId: botId,", "bot_id: botId,"),
        ("maxDepth: maxDepth", "max_pages: maxDepth"),
        ("excludePatterns: excludePatterns", "exclude_patterns: excludePatterns"),
    ]
    
    for old_field, new_field in field_updates:
        if old_field in content:
            content = content.replace(old_field, new_field)
            updates_made.append(f"✅ Updated field name: {old_field} → {new_field}")
    
    # Write updated content
    with open(dashboard_api_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Report results
    if updates_made:
        print(f"\n🎉 Successfully updated {len(updates_made)} API calls:")
        for update in updates_made:
            print(f"   {update}")
        print(f"\n📝 Updated file: {dashboard_api_file}")
        print(f"📁 Backup saved: {backup_file}")
        return True
    else:
        print("ℹ️  No updates needed - API calls already match FastAPI backend")
        # Remove backup if no changes were made
        if backup_file.exists():
            backup_file.unlink()
        return True

def create_env_template():
    """Create a .env template for the dashboard"""
    
    dashboard_dir = Path("../dashboard")
    if not dashboard_dir.exists():
        print("❌ Dashboard directory not found")
        return False
    
    env_file = dashboard_dir / ".env"
    env_example = dashboard_dir / ".env.example"
    
    env_content = """# Dashboard Environment Configuration
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_SUPABASE_URL=https://qpfljbjbyuiymeqghvsz.supabase.co
REACT_APP_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwZmxqYmpieXVpeW1lcWdodnN6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3NjgyMjcsImV4cCI6MjA2OTM0NDIyN30.BrsW0JTfNfa_u7S_rJgXIEHkYmJiTmvSUcAdvn1Cv1I
"""
    
    # Create .env.example
    with open(env_example, 'w', encoding='utf-8') as f:
        f.write(env_content)
    print(f"✅ Created dashboard environment template: {env_example}")
    
    # Create .env if it doesn't exist
    if not env_file.exists():
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ Created dashboard environment file: {env_file}")
    else:
        print(f"ℹ️  Dashboard .env file already exists: {env_file}")
    
    return True

def main():
    """Main function"""
    print("=" * 60)
    print("Dashboard API Update Script")
    print("=" * 60)
    print()
    
    # Update API calls
    api_success = update_dashboard_api()
    
    print()
    
    # Create environment files
    env_success = create_env_template()
    
    print()
    print("=" * 60)
    
    if api_success and env_success:
        print("🎉 Dashboard update completed successfully!")
        print()
        print("Next steps:")
        print("1. Review the updated API calls in dashboard/src/services/api.js")
        print("2. Update the dashboard .env file with your actual API URL if different")
        print("3. Start the FastAPI backend: python main.py")
        print("4. Start the dashboard: cd ../dashboard && npm start")
        print("5. Test all functionality to ensure integration works")
    else:
        print("❌ Some updates failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()