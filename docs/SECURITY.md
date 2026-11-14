# Security Policy

## Supported Versions

Currently, only the latest version of Dijital Kütüphane is actively supported with security updates.

| Version | Supported          |
|---------|--------------------|
| 1.0.0   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

### How to Report

**Do NOT** open a public issue for security vulnerabilities.

Instead, please report security vulnerabilities privately via [GitHub Private Vulnerability Reporting](https://github.com/fatih-es/dijital-kutuphane/security/advisories/new).

If Private Vulnerability Reporting is not accessible, you may open a confidential advisory request or contact the maintainers via [GitHub Security](https://github.com/fatih-es/dijital-kutuphane/security).

Include the following information:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- If possible, a suggested fix or mitigation

### What to Expect

- You will receive an acknowledgment of your report within 48 hours
- We will investigate the vulnerability
- We will work on a fix and coordinate disclosure with you
- We will aim to release a fix within a reasonable timeframe
- We will credit you for the discovery (unless you prefer otherwise)

### Security Best Practices

When deploying Dijital Kütüphane, ensure you:

1. **Change default secrets**:
   - Set a strong `SESSION_SECRET` in `.env`
   - Use a strong `ADMIN_TOKEN` if needed
   - Set a strong `ACCESS_PASSWORD` for library access

2. **Environment variables**:
   ```env
   SESSION_SECRET=<generate-secure-random-string>
   ADMIN_TOKEN=<if-needed>
   ACCESS_PASSWORD=<strong-password>
   COOKIE_SECURE=1  # Set to 1 when using HTTPS
   ```

3. **Network security**:
   - Use HTTPS in production
   - Configure proper firewall rules
   - Don't expose the application directly to the internet without a reverse proxy

4. **API keys**:
   - Never commit `.env` or `config.json` with real API keys
   - Rotate API keys regularly
   - Use environment-specific keys for development/staging/production

5. **File uploads**:
   - The application has built-in file size limits
   - File types are validated
   - Path traversal protection is enabled
   - Consider additional virus scanning for production deployments

6. **Dependencies**:
   - Keep dependencies updated
   - Review security advisories for dependencies
   - Use `pip-audit` or similar tools to check for vulnerabilities

### Known Security Features

Dijital Kütüphane includes the following security features:

- **Origin validation**: Prevents CSRF attacks
- **Path traversal protection**: Validates file paths
- **Rate limiting**: Limits login attempts and API requests
- **Session management**: Secure session tokens with expiration
- **Input validation**: File type and size validation
- **SQL injection prevention**: Parameterized queries
- **XSS protection**: Jinja2 auto-escaping

### Security Audits

If you're interested in conducting a security audit of this project, please contact the maintainers via [GitHub Security Advisories](https://github.com/fatih-es/dijital-kutuphane/security/advisories) first to coordinate.

## Security Advisories

Past security advisories will be documented here as needed.

---

Thank you for helping keep Dijital Kütüphane secure! 🔒
