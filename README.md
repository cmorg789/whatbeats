# WhatBeats

A game where players suggest items that beat the current item, judged by an LLM.

## Documentation

The complete documentation for this project has been moved to the main `/docs/` folder in the root directory.

Please visit the [Documentation Index](/docs/README.md) for comprehensive information about the project.

## Quick Links

- [Architecture Overview](/docs/architecture/overview.md)
- [Frontend Setup](/docs/frontend/setup.md)
- [Backend Services](/docs/backend/services.md)
- [Game Flow Sequence](/docs/diagrams/game_flow_sequence.md)

## Running the Application

Use the provided run script to start both the backend and frontend servers:

```bash
./run.sh
```

This will:
1. Check if MongoDB is running and start it if needed
2. Start the backend server
3. Start the frontend server
4. Open the application in your web browser

## Security Features

The WhatBeats application implements several security features to protect against common web vulnerabilities:

### Key Security Measures

- **Input Validation**: All user inputs are validated and sanitized to prevent injection attacks
- **XSS Protection**: Frontend uses DOMPurify and safe DOM manipulation to prevent cross-site scripting
- **Prompt Injection Protection**: LLM prompts use clear boundaries and input sanitization
- **Authentication**: Admin endpoints are protected with API key authentication
- **CORS Configuration**: CORS is restricted to specific origins for improved security
- **Error Handling**: Generic error responses prevent information disclosure
- **Security Headers**: HTTP security headers protect against various attacks

### Security Verification

To verify the security of the application:

1. Run the security tests:
   ```bash
   python whatbeats/security_tests.py
   ```

2. Review the security verification documentation:
   ```bash
   cat security_verification.md
   ```

For more details on the security features and testing procedures, see the [Security Verification Plan](../security_verification.md).

### Security Best Practices

When developing or extending the WhatBeats application, follow these security best practices:

1. **Validate all user inputs** on both client and server sides
2. **Sanitize data** before displaying it in the browser
3. **Use secure LLM prompting techniques** with clear boundaries
4. **Keep dependencies updated** to avoid known vulnerabilities
5. **Implement proper authentication** for sensitive endpoints
6. **Use HTTPS** in production environments
7. **Follow the principle of least privilege** when designing new features