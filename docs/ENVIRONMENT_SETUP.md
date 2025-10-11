# Environment Setup Guide

This guide explains how to set up and configure the Memic Backend application for different environments (development, UAT, and production).

## Overview

The application supports three environments:
- **dev**: Local development environment
- **uat**: User Acceptance Testing environment  
- **prod**: Production environment

Each environment has its own configuration file and security requirements.

## Quick Start

### 1. Copy Environment Template

```bash
# For development
cp .env.example .env.dev

# For UAT (when ready)
cp .env.example .env.uat

# For production (when ready)
cp .env.example .env.prod
```

### 2. Set Environment Variable

```bash
# For development
export APP_ENV=dev

# For UAT
export APP_ENV=uat

# For production
export APP_ENV=prod
```

### 3. Fill in Configuration Values

Edit the appropriate `.env` file with your actual values (see sections below for details).

## Development Environment Setup

### Prerequisites

1. **Python 3.14+** (installed via pyenv)
2. **PostgreSQL** (local installation)
3. **API Keys** (see below)

### Required API Keys for Development

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. **IMPORTANT**: Set spending limits in the OpenAI dashboard:
   - Go to [Usage Limits](https://platform.openai.com/account/billing/limits)
   - Set monthly limit to $10-20 for development
4. Add the key to `.env.dev`:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

#### JWT Secret Key
Generate a secure random key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Add to `.env.dev`:
```
JWT_SECRET_KEY=your-generated-key-here
```

#### Encryption Key
Generate another secure random key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Add to `.env.dev`:
```
ENCRYPTION_KEY=your-generated-key-here
```

### Database Setup

1. Install PostgreSQL locally
2. Create a development database:
   ```sql
   CREATE DATABASE memic_dev_db;
   CREATE USER memic_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE memic_dev_db TO memic_user;
   ```
3. Update `.env.dev`:
   ```
   DATABASE_URL=postgresql://memic_user:your_password@localhost/memic_dev_db
   ```

### Running the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment
export APP_ENV=dev

# Run the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## UAT Environment Setup

UAT (User Acceptance Testing) environment should mirror production as closely as possible.

### Configuration
- Use staging API keys from all third-party services
- Set `DEBUG=false`
- Use production-like database
- Restrict CORS origins to UAT domains

### Security Considerations
- All secrets should be stored in Azure Key Vault
- No `.env.uat` file should be committed to git
- Access should be restricted to authorized personnel only

## Production Environment Setup

Production environment requires the highest security standards.

### Security Requirements
- **NO** `.env.prod` file should exist in the repository
- All secrets stored in Azure Key Vault
- Environment variables set at deployment level
- Restricted CORS origins
- `DEBUG=false`
- Comprehensive logging and monitoring

### Azure Key Vault Integration
1. Create Azure Key Vault instance
2. Store all secrets in Key Vault:
   - `openai-api-key`
   - `jwt-secret-key`
   - `encryption-key`
   - `stripe-secret-key`
   - `sendgrid-api-key`
   - `database-url`
3. Configure application to read from Key Vault

## Security Best Practices

### For Developers
1. **Never commit real secrets** to git
2. **Use separate API keys** for each environment
3. **Set spending limits** on development API keys
4. **Use test/sandbox modes** for third-party services in dev
5. **Rotate keys regularly**

### For Production
1. **Use Azure Key Vault** for all secrets
2. **Implement key rotation** policies
3. **Monitor API usage** and spending
4. **Restrict access** to production secrets
5. **Audit all secret access**

## Troubleshooting

### Common Issues

#### "Required secret is missing" error
- Check that all required environment variables are set
- Verify the correct `.env` file is being used
- Ensure `APP_ENV` is set correctly

#### Database connection failed
- Verify PostgreSQL is running
- Check database credentials in `.env` file
- Ensure database exists and user has permissions

#### API key not working
- Verify the key is correct and active
- Check if spending limits are reached
- Ensure you're using the right key for the environment

### Getting Help

1. Check the application logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure you're using the right environment file
4. Contact the development team for production issues

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `APP_ENV` | Yes | Environment (dev/uat/prod) | `dev` |
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `OPENAI_API_KEY` | Yes | OpenAI API key | `sk-...` |
| `JWT_SECRET_KEY` | Yes | JWT signing key | `random-string` |
| `ENCRYPTION_KEY` | Yes | Data encryption key | `random-string` |
| `STRIPE_SECRET_KEY` | No | Stripe API key | `sk_test_...` |
| `SENDGRID_API_KEY` | No | SendGrid API key | `SG.xxx` |
| `DEBUG` | No | Debug mode | `true`/`false` |
| `CORS_ORIGINS` | No | Allowed CORS origins | `*` or `https://domain.com` |

