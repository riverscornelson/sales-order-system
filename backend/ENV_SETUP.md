# Environment Setup Guide

## Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-proj-your-actual-key-here
   ```

3. Get your OpenAI API key from: https://platform.openai.com/api-keys

## Security Best Practices

- **NEVER** commit `.env` files to version control
- **NEVER** share your API keys publicly
- **ALWAYS** use environment-specific `.env` files (.env.local, .env.production)
- **ROTATE** API keys regularly
- **USE** secret management tools in production (e.g., Google Secret Manager, AWS Secrets Manager)

## Required Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM operations | Yes | - |
| `DATABASE_URL` | Database connection string | No | sqlite:///./sales_orders.db |
| `ENVIRONMENT` | Environment name (development/staging/production) | No | production |
| `DEBUG` | Enable debug logging | No | false |

## Validation

The application will validate your configuration on startup and provide clear error messages if anything is missing or incorrect.

## Troubleshooting

If you see "Configuration Error" on startup:
1. Check that your `.env` file exists
2. Verify your OpenAI API key is valid
3. Ensure no typos in environment variable names
4. Check that sensitive values aren't placeholder text