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

// Admin credentials from environment variables with fallbacks
const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'securepassword';

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

/**
 * Check if a request is for an admin resource
 * @param {string} url - The request URL
 * @returns {boolean} True if the URL is for an admin resource
 */
function isAdminResource(url) {
    return url === '/admin' ||
           url === '/admin.html' ||
           url.startsWith('/admin/');
}

/**
 * Verify HTTP Basic Authentication credentials
 * @param {string} authHeader - The Authorization header
 * @returns {boolean} True if credentials are valid
 */
function verifyCredentials(authHeader) {
    if (!authHeader || !authHeader.startsWith('Basic ')) {
        return false;
    }

    // Extract and decode the credentials
    const base64Credentials = authHeader.split(' ')[1];
    const credentials = Buffer.from(base64Credentials, 'base64').toString('utf-8');
    const [username, password] = credentials.split(':');

    // Verify against expected credentials
    return username === ADMIN_USERNAME && password === ADMIN_PASSWORD;
}

// Create the server
const server = http.createServer((req, res) => {
    console.log(`Request: ${req.method} ${req.url}`);
    
    // Handle CORS preflight requests
    if (req.method === 'OPTIONS') {
        res.writeHead(204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization',
            'Access-Control-Max-Age': '86400' // 24 hours
        });
        res.end();
        return;
    }
    
    // Check if the request is for an admin resource
    if (isAdminResource(req.url)) {
        // Get the Authorization header
        const authHeader = req.headers.authorization;
        
        // If no credentials or invalid credentials, request authentication
        if (!verifyCredentials(authHeader)) {
            res.writeHead(401, {
                'WWW-Authenticate': 'Basic realm="Admin Access"',
                'Content-Type': 'text/plain'
            });
            res.end('Authentication required for admin access');
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
            // Success - Add CORS headers
            res.writeHead(200, {
                'Content-Type': contentType,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, Authorization'
            });
            res.end(content, 'utf-8');
        }
    });
});

// Start the server
server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
    console.log(`Admin interface available at http://localhost:${PORT}/admin`);
    console.log(`Press Ctrl+C to stop the server`);
});