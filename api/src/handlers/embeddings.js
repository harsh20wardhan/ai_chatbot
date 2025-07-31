import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_KEY);
};

// Generate embeddings for documents
export const generateEmbeddings = async ({ request, user, env, corsHeaders }) => {
  try {
    const { documentIds, botId } = await request.json();
    
    if (!botId) {
      return new Response(JSON.stringify({ error: 'Bot ID is required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }

    if (!documentIds || !Array.isArray(documentIds) || documentIds.length === 0) {
      return new Response(JSON.stringify({ error: 'At least one document ID is required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    const supabase = getSupabase(env);
    
    // Verify bot ownership
    const { error: botError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();
      
    if (botError) {
      return new Response(JSON.stringify({ error: 'Bot not found or access denied' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Verify document ownership
    const { data: documents, error: docsError } = await supabase
      .from('documents')
      .select('id, file_path, file_type, status')
      .in('id', documentIds)
      .eq('bot_id', botId)
      .eq('user_id', user.id);
      
    if (docsError) {
      return new Response(JSON.stringify({ error: docsError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    if (documents.length === 0) {
      return new Response(JSON.stringify({ error: 'No valid documents found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Check if all documents are in a processed state
    const unprocessedDocs = documents.filter(doc => doc.status !== 'processed');
    if (unprocessedDocs.length > 0) {
      return new Response(JSON.stringify({ 
        error: 'Some documents are not ready for embedding',
        unprocessed_documents: unprocessedDocs.map(d => d.id)
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Create an embedding job
    const { data: job, error: jobError } = await supabase
      .from('embedding_jobs')
      .insert([
        {
          bot_id: botId,
          user_id: user.id,
          document_ids: documentIds,
          status: 'pending',
          created_at: new Date().toISOString()
        }
      ])
      .select()
      .single();
      
    if (jobError) {
      return new Response(JSON.stringify({ error: jobError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Update documents to mark them as embedding
    await supabase
      .from('documents')
      .update({ status: 'embedding' })
      .in('id', documentIds)
      .eq('user_id', user.id);
      
    // Trigger the embeddings microservice
    try {
      const response = await fetch(`${env.EMBEDDINGS_SERVICE_URL}/embed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.EMBEDDINGS_SERVICE_KEY}`
        },
        body: JSON.stringify({
          job_id: job.id,
          bot_id: botId,
          document_ids: documentIds
        })
      });
      
      if (!response.ok) {
        // Update job status to failed
        await supabase
          .from('embedding_jobs')
          .update({ status: 'failed', error: 'Failed to start embedding service' })
          .eq('id', job.id);
          
        // Revert documents back to processed state
        await supabase
          .from('documents')
          .update({ status: 'processed' })
          .in('id', documentIds)
          .eq('user_id', user.id);
          
        return new Response(JSON.stringify({ 
          error: 'Failed to start embedding service',
          job_id: job.id
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
    } catch (serviceError) {
      // Update job status to failed
      await supabase
        .from('embedding_jobs')
        .update({ status: 'failed', error: 'Embedding service unavailable' })
        .eq('id', job.id);
        
      // Revert documents back to processed state
      await supabase
        .from('documents')
        .update({ status: 'processed' })
        .in('id', documentIds)
        .eq('user_id', user.id);
        
      return new Response(JSON.stringify({ 
        error: 'Embedding service unavailable',
        job_id: job.id
      }), {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ 
      message: 'Embedding job started successfully',
      job_id: job.id
    }), {
      status: 202,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to process embedding request' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get the status of an embedding job
export const getEmbeddingStatus = async ({ params, user, env, corsHeaders }) => {
  try {
    const { jobId } = params;
    
    const supabase = getSupabase(env);
    const { data, error } = await supabase
      .from('embedding_jobs')
      .select('*')
      .eq('id', jobId)
      .eq('user_id', user.id)
      .single();
      
    if (error) {
      return new Response(JSON.stringify({ error: 'Embedding job not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ job: data }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to get embedding status' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Delete embeddings for a bot
export const deleteEmbeddings = async ({ params, user, env, corsHeaders }) => {
  try {
    const { botId } = params;
    
    const supabase = getSupabase(env);
    
    // Verify bot ownership
    const { error: botError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();
      
    if (botError) {
      return new Response(JSON.stringify({ error: 'Bot not found or access denied' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Reset the status of all embedded documents back to processed
    await supabase
      .from('documents')
      .update({ status: 'processed' })
      .eq('bot_id', botId)
      .eq('user_id', user.id)
      .eq('status', 'embedded');
      
    // Delete embeddings from Qdrant
    try {
      const response = await fetch(`${env.EMBEDDINGS_SERVICE_URL}/delete_all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.EMBEDDINGS_SERVICE_KEY}`
        },
        body: JSON.stringify({
          bot_id: botId
        })
      });
      
      if (!response.ok) {
        return new Response(JSON.stringify({ error: 'Failed to delete embeddings' }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
    } catch (serviceError) {
      return new Response(JSON.stringify({ error: 'Embedding service unavailable' }), {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ message: 'Embeddings deleted successfully' }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to delete embeddings' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 