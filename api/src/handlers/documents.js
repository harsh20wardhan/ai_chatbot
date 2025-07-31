import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_KEY);
};

// Upload a document
export const uploadDocument = async ({ request, user, env, corsHeaders }) => {
  try {
    // Parse the form data
    const formData = await request.formData();
    const file = formData.get('file');
    const botId = formData.get('botId');
    
    if (!file) {
      return new Response(JSON.stringify({ error: 'No file provided' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    if (!botId) {
      return new Response(JSON.stringify({ error: 'Bot ID is required' }), {
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
    
    // Upload file to Supabase Storage
    const fileName = file.name;
    const fileType = fileName.split('.').pop().toLowerCase();
    const filePath = `${user.id}/${botId}/${Date.now()}_${fileName}`;
    
    // Check if file type is supported
    const supportedTypes = ['pdf', 'txt', 'docx', 'md', 'html'];
    if (!supportedTypes.includes(fileType)) {
      return new Response(JSON.stringify({ 
        error: `Unsupported file type. Supported types: ${supportedTypes.join(', ')}` 
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Upload to Supabase Storage
    const { data: storageData, error: storageError } = await supabase
      .storage
      .from('documents')
      .upload(filePath, file, {
        contentType: file.type,
        upsert: true
      });
      
    if (storageError) {
      return new Response(JSON.stringify({ error: storageError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Create document record in database
    const { data: document, error: docError } = await supabase
      .from('documents')
      .insert([
        {
          bot_id: botId,
          user_id: user.id,
          file_name: fileName,
          file_type: fileType,
          file_path: filePath,
          file_size: file.size,
          status: 'pending',
          created_at: new Date().toISOString()
        }
      ])
      .select()
      .single();
      
    if (docError) {
      // Delete the uploaded file if record creation fails
      await supabase.storage.from('documents').remove([filePath]);
      
      return new Response(JSON.stringify({ error: docError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Trigger the parser microservice
    try {
      const response = await fetch(`${env.PARSER_SERVICE_URL}/parse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.PARSER_SERVICE_KEY}`
        },
        body: JSON.stringify({
          document_id: document.id,
          file_path: filePath,
          file_type: fileType,
          bot_id: botId
        })
      });
      
      if (!response.ok) {
        // Update document status to failed
        await supabase
          .from('documents')
          .update({ status: 'failed', error: 'Failed to start parser service' })
          .eq('id', document.id);
          
        return new Response(JSON.stringify({ 
          error: 'Failed to start parser service',
          document_id: document.id
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
    } catch (serviceError) {
      // Update document status to failed
      await supabase
        .from('documents')
        .update({ status: 'failed', error: 'Parser service unavailable' })
        .eq('id', document.id);
        
      return new Response(JSON.stringify({ 
        error: 'Parser service unavailable',
        document_id: document.id
      }), {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ 
      message: 'Document uploaded successfully',
      document_id: document.id,
      file_name: fileName
    }), {
      status: 202,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to process document upload' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get all documents for a bot
export const getDocuments = async ({ request, user, env, corsHeaders }) => {
  try {
    const url = new URL(request.url);
    const botId = url.searchParams.get('botId');
    
    if (!botId) {
      return new Response(JSON.stringify({ error: 'Bot ID is required' }), {
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
    
    // Get documents for the bot
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('bot_id', botId)
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });
      
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ documents: data }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve documents' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get a specific document
export const getDocument = async ({ params, user, env, corsHeaders }) => {
  try {
    const { documentId } = params;
    
    const supabase = getSupabase(env);
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .eq('id', documentId)
      .eq('user_id', user.id)
      .single();
      
    if (error) {
      return new Response(JSON.stringify({ error: 'Document not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ document: data }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve document' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Delete a document
export const deleteDocument = async ({ params, user, env, corsHeaders }) => {
  try {
    const { documentId } = params;
    
    const supabase = getSupabase(env);
    
    // Get document details
    const { data, error: fetchError } = await supabase
      .from('documents')
      .select('file_path, bot_id')
      .eq('id', documentId)
      .eq('user_id', user.id)
      .single();
      
    if (fetchError) {
      return new Response(JSON.stringify({ error: 'Document not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Delete file from storage
    const { error: storageError } = await supabase
      .storage
      .from('documents')
      .remove([data.file_path]);
      
    if (storageError) {
      console.error('Failed to delete file from storage:', storageError);
      // Continue with deletion from database even if storage deletion fails
    }
    
    // Delete document from database
    const { error: deleteError } = await supabase
      .from('documents')
      .delete()
      .eq('id', documentId)
      .eq('user_id', user.id);
      
    if (deleteError) {
      return new Response(JSON.stringify({ error: deleteError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // If document has already been embedded, delete embeddings from Qdrant
    try {
      await fetch(`${env.EMBEDDINGS_SERVICE_URL}/documents/${documentId}/delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.EMBEDDINGS_SERVICE_KEY}`
        },
        body: JSON.stringify({
          bot_id: data.bot_id
        })
      });
    } catch (serviceError) {
      console.error('Failed to delete embeddings:', serviceError);
      // Continue even if embeddings deletion fails
    }
    
    return new Response(JSON.stringify({ message: 'Document deleted successfully' }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to delete document' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 