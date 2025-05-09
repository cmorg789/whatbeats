/**
 * Static file server for the "What Beats Rock?" frontend
 * With HTTP Basic Authentication for admin routes
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from root directory
const rootDir = path.resolve(__dirname, '..');
dotenv.config({ path: path.join(rootDir, '.env') });

// Port to run the server on
const PORT = 3000;

// MIME types for different file extensions
const MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
};


// Create the server
const server = http.createServer((req, res) => {
    console.log(`Request: ${req.method} ${req.url}`);
    
    // Handle preflight requests (now handled by Nginx reverse proxy)
    if (req.method === 'OPTIONS') {
        res.writeHead(204, {
            // Content Security Policy
            'Content-Security-Policy': `default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; connect-src 'self' http://localhost http://${process.env.DOMAIN || 'localhost'}`,
            // Additional security headers
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'Referrer-Policy': 'no-referrer-when-downgrade',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
        });
        res.end();
        return;
    }
    
    // If URL is just /admin, redirect to admin.html
    if (req.url === '/admin') {
        res.writeHead(302, {
            'Location': '/admin.html'
        });
        res.end();
        return;
    }
    
    // Get the file path
    let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
    
    // Get the file extension
    const extname = path.extname(filePath);
    
    // Set the content type based on the file extension
    const contentType = MIME_TYPES[extname] || 'application/octet-stream';
    
    // Read the file
    fs.readFile(filePath, (err, content) => {
        if (err) {
            if (err.code === 'ENOENT') {
                // File not found
                console.error(`File not found: ${filePath}`);
                res.writeHead(404);
                res.end('404 Not Found');
            } else {
                // Server error
                console.error(`Server error: ${err.code}`);
                res.writeHead(500);
                res.end(`Server Error: ${err.code}`);
            }
        } else {
            // Success - Add security headers only (CORS now handled by Nginx)
            res.writeHead(200, {
                'Content-Type': contentType,
                // Content Security Policy
                'Content-Security-Policy': `default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; connect-src 'self' http://localhost http://${process.env.DOMAIN || 'localhost'}`,
                // Additional security headers
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'Referrer-Policy': 'no-referrer-when-downgrade',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
            });
            res.end(content, 'utf-8');
        }
    });
});

// Start the server
server.listen(PORT, () => {
    console.log(`Server running at http://${process.env.DOMAIN || 'localhost'}:${PORT}/`);
    console.log(`Admin interface available at http://${process.env.DOMAIN || 'localhost'}:${PORT}/admin`);
    console.log(`Press Ctrl+C to stop the server`);
});