import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client for public operations
const getPublicSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_ANON_KEY);
};

// Helper to initialize Supabase client for admin operations
const getAdminSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);
};

// User registration
export const register = async ({ request, env, corsHeaders }) => {
  try {
    const { email, password, name } = await request.json();
    
    if (!email || !password) {
      return new Response(JSON.stringify({ error: 'Email and password are required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Log connection details for debugging (don't include sensitive info)
    console.log(`Connecting to Supabase at: ${env.SUPABASE_URL}`);
    console.log(`Email: ${email}, Has Password: ${password ? 'Yes' : 'No'}, Name: ${name || 'Not provided'}`);
    
    // Check if env variables are set
    if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) {
      console.error('Missing required Supabase environment variables');
      return new Response(JSON.stringify({ 
        error: 'Server configuration error',
        details: 'Missing required Supabase configuration'
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Use the public client for signup as recommended by Supabase
    const supabase = getPublicSupabase(env);
    
    // Use more explicit options for debugging purposes
    const signUpOptions = {
      email,
      password,
      options: {
        data: { name },
        emailRedirectTo: `${request.headers.get('origin') || 'http://localhost:8787'}/auth/callback`
      }
    };
    
    console.log('Calling Supabase signUp with options:', JSON.stringify({
      ...signUpOptions,
      password: '[REDACTED]'
    }));
    
    const { data, error } = await supabase.auth.signUp(signUpOptions);
    
    if (error) {
      console.error('Supabase Auth Error:', JSON.stringify(error));
      return new Response(JSON.stringify({ 
        error: error.message,
        details: error.details || 'No additional details',
        code: error.code || 'unknown'
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ 
      message: 'Registration successful', 
      user: data.user
    }), {
      status: 201,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    return new Response(JSON.stringify({ 
      error: 'Failed to process registration',
      details: error.message || 'Unknown error',
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// User login
export const login = async ({ request, env, corsHeaders }) => {
  try {
    const { email, password } = await request.json();
    
    if (!email || !password) {
      return new Response(JSON.stringify({ error: 'Email and password are required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    const supabase = getPublicSupabase(env);
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    });
    
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 401,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ 
      message: 'Login successful',
      user: data.user,
      session: data.session
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to process login' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// User logout
export const logout = async ({ request, env, corsHeaders }) => {
  try {
    const { token } = await request.json();
    
    if (!token) {
      return new Response(JSON.stringify({ error: 'Token is required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    const supabase = getAdminSupabase(env);
    const { error } = await supabase.auth.admin.signOut(token);
    
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ message: 'Logout successful' }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to process logout' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get current user
export const getUser = async ({ user, corsHeaders }) => {
  try {
    return new Response(JSON.stringify({ user }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to get user information' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 

// Simple test endpoint that doesn't require Supabase
export const healthCheck = async ({ corsHeaders }) => {
  try {
    return new Response(JSON.stringify({ 
      status: 'ok', 
      message: 'Auth service is running', 
      timestamp: new Date().toISOString() 
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Health check failed' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 