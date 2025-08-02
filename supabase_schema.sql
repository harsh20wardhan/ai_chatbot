-- Create bots table
CREATE TABLE bots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  website_url TEXT,
  settings JSONB DEFAULT '{}',
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ
);

-- Create crawl_jobs table
CREATE TABLE crawl_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  max_depth INTEGER NOT NULL DEFAULT 3,
  exclude_patterns TEXT[] DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'pending',
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- Create crawled_pages table to store crawled content
CREATE TABLE crawled_pages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  crawl_job_id UUID NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
  bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  content_length INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, embedded, failed
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  embedded_at TIMESTAMPTZ
);

-- Create embedding_chunks table to store text chunks and their embeddings
CREATE TABLE embedding_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  crawled_page_id UUID NOT NULL REFERENCES crawled_pages(id) ON DELETE CASCADE,
  bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  chunk_text TEXT NOT NULL,
  chunk_length INTEGER NOT NULL,
  embedding_vector REAL[], -- Store the actual embedding vector
  qdrant_point_id TEXT, -- Store the Qdrant point ID for reference
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create realtime_crawl_sessions table for WebSocket connections
CREATE TABLE realtime_crawl_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  crawl_job_id UUID NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
  bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  session_token TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active', -- active, closed, expired
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ
);

-- Create documents table
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size BIGINT,
  status TEXT NOT NULL DEFAULT 'pending',
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  processed_at TIMESTAMPTZ
);

-- Create document_chunks table to store document content chunks
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  chunk_text TEXT NOT NULL,
  chunk_length INTEGER NOT NULL,
  embedding_vector REAL[], -- Store the actual embedding vector
  qdrant_point_id TEXT, -- Store the Qdrant point ID for reference
  embedded_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create embedding_jobs table
CREATE TABLE embedding_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  document_ids UUID[] NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- Create conversations table
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bot_id UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  title TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ
);

-- Create messages table
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Row Level Security (RLS) policies
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawl_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawled_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE embedding_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE realtime_crawl_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE embedding_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- RLS policy for bots
CREATE POLICY bots_user_policy ON bots
  USING (user_id = auth.uid());

-- RLS policy for crawl_jobs
CREATE POLICY crawl_jobs_user_policy ON crawl_jobs
  USING (user_id = auth.uid());

-- RLS policy for crawled_pages
CREATE POLICY crawled_pages_user_policy ON crawled_pages
  USING (user_id = auth.uid());

-- RLS policy for embedding_chunks
CREATE POLICY embedding_chunks_user_policy ON embedding_chunks
  USING (user_id = auth.uid());

-- RLS policy for realtime_crawl_sessions
CREATE POLICY realtime_crawl_sessions_user_policy ON realtime_crawl_sessions
  USING (user_id = auth.uid());

-- RLS policy for documents
CREATE POLICY documents_user_policy ON documents
  USING (user_id = auth.uid());
  
-- RLS policy for document_chunks
CREATE POLICY document_chunks_user_policy ON document_chunks
  USING (user_id = auth.uid());

-- RLS policy for embedding_jobs
CREATE POLICY embedding_jobs_user_policy ON embedding_jobs
  USING (user_id = auth.uid());

-- RLS policy for conversations
CREATE POLICY conversations_bot_policy ON conversations
  USING (bot_id IN (SELECT id FROM bots WHERE user_id = auth.uid()));

-- RLS policy for messages
CREATE POLICY messages_conversation_policy ON messages
  USING (conversation_id IN (SELECT id FROM conversations WHERE bot_id IN (SELECT id FROM bots WHERE user_id = auth.uid())));

-- Create storage buckets
INSERT INTO storage.buckets (id, name, public) VALUES ('documents', 'documents', false);

-- RLS policy for storage
CREATE POLICY documents_storage_policy ON storage.objects
  FOR ALL USING (
    -- Extract user_id from storage path (format: {user_id}/{bot_id}/{filename})
    SPLIT_PART(name, '/', 1) = auth.uid()::text
  );

-- Create indexes for better performance
CREATE INDEX idx_crawled_pages_crawl_job_id ON crawled_pages(crawl_job_id);
CREATE INDEX idx_crawled_pages_bot_id ON crawled_pages(bot_id);
CREATE INDEX idx_embedding_chunks_crawled_page_id ON embedding_chunks(crawled_page_id);
CREATE INDEX idx_embedding_chunks_bot_id ON embedding_chunks(bot_id);
CREATE INDEX idx_realtime_crawl_sessions_session_token ON realtime_crawl_sessions(session_token);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_bot_id ON document_chunks(bot_id); 