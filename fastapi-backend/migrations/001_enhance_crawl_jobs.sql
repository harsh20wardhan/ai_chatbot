-- Migration: Enhance crawl_jobs table with deep crawling capabilities
-- Date: 2024-01-XX
-- Description: Add new fields for enhanced crawling functionality

-- Add new columns to existing crawl_jobs table
ALTER TABLE crawl_jobs 
ADD COLUMN IF NOT EXISTS max_pages INTEGER DEFAULT 100,
ADD COLUMN IF NOT EXISTS include_patterns TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS respect_robots_txt BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS delay_between_requests REAL DEFAULT 1.0;

-- Update existing records to have reasonable defaults
UPDATE crawl_jobs 
SET 
    max_pages = COALESCE(max_pages, 100),
    include_patterns = COALESCE(include_patterns, '{}'),
    respect_robots_txt = COALESCE(respect_robots_txt, TRUE),
    delay_between_requests = COALESCE(delay_between_requests, 1.0)
WHERE max_pages IS NULL 
   OR include_patterns IS NULL 
   OR respect_robots_txt IS NULL 
   OR delay_between_requests IS NULL;

-- Make new columns NOT NULL after setting defaults
ALTER TABLE crawl_jobs 
ALTER COLUMN max_pages SET NOT NULL,
ALTER COLUMN include_patterns SET NOT NULL,
ALTER COLUMN respect_robots_txt SET NOT NULL,
ALTER COLUMN delay_between_requests SET NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN crawl_jobs.max_pages IS 'Maximum number of pages to crawl';
COMMENT ON COLUMN crawl_jobs.include_patterns IS 'URL patterns to include in crawling';
COMMENT ON COLUMN crawl_jobs.respect_robots_txt IS 'Whether to respect robots.txt rules';
COMMENT ON COLUMN crawl_jobs.delay_between_requests IS 'Delay between requests in seconds';

-- Create index for better performance on common queries
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_user_bot_status ON crawl_jobs(user_id, bot_id, status);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_created_at ON crawl_jobs(created_at DESC);
