export class Router {
  constructor() {
    this.routes = [];
    this.middlewares = [];
  }

  use(middleware) {
    this.middlewares.push(middleware);
    return this;
  }

  get(path, ...handlers) {
    return this.addRoute('GET', path, handlers);
  }

  post(path, ...handlers) {
    return this.addRoute('POST', path, handlers);
  }

  put(path, ...handlers) {
    return this.addRoute('PUT', path, handlers);
  }

  delete(path, ...handlers) {
    return this.addRoute('DELETE', path, handlers);
  }

  addRoute(method, path, handlers) {
    this.routes.push({ method, path, handlers });
    return this;
  }

  async handle(request, env, ctx) {
    const url = new URL(request.url);
    const method = request.method;
    const path = url.pathname;

    // Create request context
    const context = {
      request,
      env,
      ctx,
      url
    };

    // Apply global middlewares first, especially for OPTIONS requests
    for (const middleware of this.middlewares) {
      const result = await middleware(context);
      if (result instanceof Response) return result;
    }

    // Special handling for OPTIONS requests - already handled by CORS middleware
    if (method === 'OPTIONS') {
      // If we got here, it means the CORS middleware didn't return a response
      // Let's create a default OPTIONS response
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': request.headers.get('Origin') || '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Max-Age': '86400'
        }
      });
    }

    // Find matching route for non-OPTIONS requests
    const route = this.routes.find(route => {
      return route.method === method && this.matchPath(route.path, path);
    });

    if (!route) {
      return new Response('Not Found', { status: 404 });
    }
    
    // Add route params to context
    context.params = this.extractParams(route.path, path);

    try {
      // Middlewares have already been applied

      // Apply route handlers
      let result;
      for (const handler of route.handlers) {
        result = await handler(context);
        if (result instanceof Response) break;
      }

      return result instanceof Response ? result : new Response('No response returned', { status: 500 });
    } catch (error) {
      console.error('Error processing request:', error);
      return new Response('Internal Server Error', { status: 500 });
    }
  }

  matchPath(routePath, requestPath) {
    const routeParts = routePath.split('/');
    const requestParts = requestPath.split('/');

    if (routeParts.length !== requestParts.length) return false;

    return routeParts.every((part, i) => {
      if (part.startsWith(':')) return true; // Path parameter matches anything
      return part === requestParts[i];
    });
  }

  extractParams(routePath, requestPath) {
    const params = {};
    const routeParts = routePath.split('/');
    const requestParts = requestPath.split('/');

    routeParts.forEach((part, i) => {
      if (part.startsWith(':')) {
        const paramName = part.slice(1);
        params[paramName] = requestParts[i];
      }
    });

    return params;
  }
} 