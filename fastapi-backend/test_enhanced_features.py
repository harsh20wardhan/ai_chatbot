#!/usr/bin/env python3
"""
Test Script for Enhanced Crawling and Parsing Features

This script demonstrates the new enhanced crawling and parsing capabilities.
Run this script to test the improvements in content extraction and deep crawling.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from services.crawler import crawler_service
from services.parser import parser_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_enhanced_crawler():
    """Test the enhanced crawler service"""
    
    logger.info("🧪 Testing Enhanced Crawler Service...")
    
    try:
        # Test URL (replace with a real website for testing)
        test_url = "https://example.com"
        
        logger.info(f"Starting enhanced crawl of: {test_url}")
        
        # Test the enhanced crawler with depth control
        result = await crawler_service.crawl_website(
            url=test_url,
            max_pages=10,  # Small number for testing
            max_depth=3,   # Test depth control
            exclude_patterns=["/admin", "/private"],
            include_patterns=["/blog", "/docs"],
            respect_robots_txt=True,
            delay_between_requests=1.0
        )
        
        logger.info(f"✅ Enhanced crawl completed successfully!")
        logger.info(f"   Pages crawled: {result.get('pages_crawled', 0)}")
        logger.info(f"   Max depth reached: {result.get('max_depth_reached', 0)}")
        logger.info(f"   Status: {result.get('status', 'unknown')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Enhanced crawler test failed: {e}")
        return None

async def test_enhanced_parser():
    """Test the enhanced parser service"""
    
    logger.info("🧪 Testing Enhanced Parser Service...")
    
    try:
        # Create a test text file
        test_content = """
        This is a test document with multiple paragraphs.
        
        It contains various types of content including:
        - Bullet points
        - Multiple lines
        - Different formatting
        
        The enhanced parser should clean this content and create high-quality chunks.
        
        This paragraph contains more detailed information that should be preserved
        during the parsing and chunking process.
        """
        
        # Test the enhanced text processing
        cleaned_text = parser_service._enhance_text_quality(test_content)
        chunks = parser_service._enhanced_chunk_text(cleaned_text)
        
        logger.info(f"✅ Enhanced parser test completed successfully!")
        logger.info(f"   Original length: {len(test_content)} characters")
        logger.info(f"   Cleaned length: {len(cleaned_text)} characters")
        logger.info(f"   Chunks created: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            logger.info(f"   Chunk {i+1}: {len(chunk)} characters")
        
        return {
            'original_length': len(test_content),
            'cleaned_length': len(cleaned_text),
            'chunks_count': len(chunks),
            'chunks': chunks
        }
        
    except Exception as e:
        logger.error(f"❌ Enhanced parser test failed: {e}")
        return None

async def test_content_quality_improvements():
    """Test content quality improvement features"""
    
    logger.info("🧪 Testing Content Quality Improvements...")
    
    try:
        # Test noise filtering
        test_lines = [
            "This is good content",
            "",  # Empty line
            "123",  # Just numbers
            "Page 5",  # Page number
            "© 2024 Company Name",  # Copyright
            "All rights reserved",  # Legal text
            "This is more good content",
            "   ",  # Whitespace only
            "A",  # Single letter
            "Final good content line"
        ]
        
        # Test noise line detection
        noise_count = 0
        good_lines = []
        
        for line in test_lines:
            if parser_service._is_noise_line(line):
                noise_count += 1
                logger.info(f"   Filtered noise: '{line}'")
            else:
                good_lines.append(line)
        
        logger.info(f"✅ Content quality test completed successfully!")
        logger.info(f"   Total lines: {len(test_lines)}")
        logger.info(f"   Noise lines filtered: {noise_count}")
        logger.info(f"   Good lines kept: {len(good_lines)}")
        
        return {
            'total_lines': len(test_lines),
            'noise_filtered': noise_count,
            'good_lines': len(good_lines)
        }
        
    except Exception as e:
        logger.error(f"❌ Content quality test failed: {e}")
        return None

async def main():
    """Main test function"""
    
    logger.info("🚀 Starting Enhanced Features Test Suite...")
    logger.info("=" * 60)
    
    results = {}
    
    # Test enhanced parser (doesn't require external resources)
    results['parser'] = await test_enhanced_parser()
    logger.info("")
    
    # Test content quality improvements
    results['quality'] = await test_content_quality_improvements()
    logger.info("")
    
    # Test enhanced crawler (requires internet connection)
    logger.info("⚠️  Note: Crawler test requires internet connection and may take time...")
    results['crawler'] = await test_enhanced_crawler()
    logger.info("")
    
    # Summary
    logger.info("📊 Test Summary:")
    logger.info("=" * 60)
    
    if results['parser']:
        logger.info("✅ Enhanced Parser: PASSED")
    else:
        logger.info("❌ Enhanced Parser: FAILED")
    
    if results['quality']:
        logger.info("✅ Content Quality: PASSED")
    else:
        logger.info("❌ Content Quality: FAILED")
    
    if results['crawler']:
        logger.info("✅ Enhanced Crawler: PASSED")
    else:
        logger.info("❌ Enhanced Crawler: FAILED")
    
    logger.info("=" * 60)
    logger.info("🎉 Enhanced Features Test Suite completed!")

if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())
