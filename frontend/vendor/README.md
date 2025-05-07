# Vendor Libraries

This directory contains self-hosted third-party libraries used by the WhatBeats application. Self-hosting these libraries provides several security benefits:

1. **Reduced dependency on external CDNs**: Eliminates the risk of CDN outages affecting our application
2. **Control over library versions**: Prevents unexpected updates that might introduce bugs or security issues
3. **Improved privacy**: Reduces tracking of users through CDN requests
4. **Offline functionality**: Allows the application to function without internet access

## Current Libraries

- **axios.min.js**: HTTP client for making API requests
- **purify.min.js**: DOMPurify library for sanitizing HTML content

## Security Measures

### Subresource Integrity (SRI)

All vendor scripts include SRI hash checks to ensure the integrity of the files. If a file is corrupted or modified, the browser will refuse to load it.

### CDN Fallback

The application includes fallback mechanisms to load these libraries from their original CDNs if the local versions fail to load, maintaining the SRI checks.

## Maintenance

### Regular Audits

Run the following commands regularly to check for security vulnerabilities and outdated dependencies:

```bash
# Check for vulnerabilities
npm run audit

# Fix vulnerabilities (when possible)
npm run audit:fix

# Check for outdated dependencies
npm run deps:check
```

### Updating Libraries

When updating these libraries:

1. Download the latest version from the official source
2. Generate a new SRI hash using a tool like [SRI Hash Generator](https://www.srihash.org/)
3. Update the hash in both HTML files (index.html and admin.html)
4. Test thoroughly before deploying to production

## Last Updated

Date: May 7, 2025