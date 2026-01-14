// Cloudflare Workers proxy function
// Handles /proxy route for proxying web content

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  
  // Get the target URL from query parameter
  const targetUrl = url.searchParams.get('url');
  
  if (!targetUrl) {
    // If no URL parameter, redirect to proxy.html
    // Since Cloudflare Pages Functions can't easily fetch static files,
    // we redirect to the static file
    return Response.redirect(`${url.origin}/proxy.html`, 302);
  }
  
  try {
    // Validate URL
    const targetUrlObj = new URL(targetUrl);
    
    // Fetch the target URL
    const proxyRequest = new Request(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': targetUrl,
        'Origin': targetUrlObj.origin
      }
    });
    
    const response = await fetch(proxyRequest);
    
    // Check if it's HTML content
    const contentType = response.headers.get('content-type') || '';
    const isHtml = contentType.includes('text/html');
    
    if (!isHtml) {
      // For non-HTML content (images, CSS, JS, etc.), return as-is
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          'Content-Type': contentType,
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=3600'
        }
      });
    }
    
    // For HTML content, rewrite URLs
    const html = await response.text();
    
    // Get the proxy base URL
    const proxyBase = `${url.origin}/proxy?url=`;
    
    // Rewrite URLs in the HTML
    let modifiedHtml = html;
    
    // Rewrite href attributes
    modifiedHtml = modifiedHtml.replace(/href=["']([^"']+)["']/gi, (match, urlPath) => {
      if (urlPath.startsWith('javascript:') || urlPath.startsWith('mailto:') || urlPath.startsWith('#') || urlPath.startsWith('data:')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `href="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite src attributes
    modifiedHtml = modifiedHtml.replace(/src=["']([^"']+)["']/gi, (match, urlPath) => {
      if (urlPath.startsWith('data:')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `src="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite action attributes
    modifiedHtml = modifiedHtml.replace(/action=["']([^"']+)["']/gi, (match, urlPath) => {
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `action="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite CSS url() references
    modifiedHtml = modifiedHtml.replace(/url\(["']?([^"')]+)["']?\)/gi, (match, urlPath) => {
      if (urlPath.startsWith('data:') || urlPath.startsWith('#')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `url("${proxyBase}${encodeURIComponent(absoluteUrl)}")`;
      } catch (e) {
        return match;
      }
    });
    
    // Inject base tag to help with relative URLs
    modifiedHtml = modifiedHtml.replace(
      /<head[^>]*>/i,
      `<head><base href="${targetUrl}">`
    );
    
    // Return the modified HTML
    return new Response(modifiedHtml, {
      status: response.status,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-cache'
      }
    });
    
  } catch (error) {
    console.error('Proxy error:', error);
    return new Response(`Proxy error: ${error.message}`, {
      status: 500,
      headers: {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
}
