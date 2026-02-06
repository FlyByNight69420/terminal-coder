# Bootstrap Guide

## Prerequisites

| Tool | Install | Verify |
|------|---------|--------|
| Node.js 20+ | `nvm install 20` | `node --version` |
| pnpm | `npm install -g pnpm` | `pnpm --version` |
| Docker | See docker.com | `docker info` |

## Scoped Credentials

### GitHub

Create a personal access token with `repo` scope.

**Verify:** `gh auth status`

### Database

Set up a local PostgreSQL database.

**Verify:** `pg_isready -h localhost`

## Environment Configuration

### Populate .env file

Create a `.env` file with the following variables:

- `DATABASE_URL` - PostgreSQL connection string
- `API_KEY` - Your API key for the service
- `NODE_ENV` - Set to "development"
