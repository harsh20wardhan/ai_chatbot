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

    // Find matching route
    const route = this.routes.find(route => {
      return route.method === method && this.matchPath(route.path, path);
    });

    if (!route) {
      return new Response('Not Found', { status: 404 });
    }

    // Create request context
    const context = {
      request,
      env,
      ctx,
      params: this.extractParams(route.path, path),
      url
    };

    try {
      // Apply global middlewares
      for (const middleware of this.middlewares) {
        const result = await middleware(context);
        if (result instanceof Response) return result;
      }

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