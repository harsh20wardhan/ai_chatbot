export const corsMiddleware = async (context) => {
  const { request } = context;
  
  // Get the origin from the request
  const origin = request.headers.get('Origin') || '*';
  
  // Define allowed origins
  const allowedOrigins = [
    'http://localhost:3000',
    'http://localhost:8787',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8787'
  ];
  
  // Check if the origin is allowed - for development, allow all origins
  const isAllowedOrigin = true; // allowedOrigins.includes(origin) || origin === '*';
  
  // Set the appropriate CORS origin
  const corsOrigin = isAllowedOrigin ? origin : allowedOrigins[0];
  
  // Create CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': corsOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
    'Access-Control-Allow-Credentials': 'true',
  };
  
  // Handle preflight requests
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        ...corsHeaders,
        'Access-Control-Max-Age': '86400',
      }
    });
  }
  
  // Add CORS headers to all responses
  context.corsHeaders = corsHeaders;
}; 