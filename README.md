# CnCNet GitHub Webhook Discord Bot

This Discord bot integrates with GitHub webhooks to deliver real-time notifications about various GitHub events to the CnCNet Discord server.

### Event Types
The bot supports various GitHub event types, including:

- Push: Notifies when code is pushed to a repository.
- Pull Request: Notifies when a pull request is opened, closed, or updated.
- Issues: Notifies when issues are opened, closed, or updated.
- Forks: Notifies when someone forks a repository.
- Stars: Notifies when someone stars a repository.

### Deployment
1. Copy `.env.example` to `.env` and fill in credentials. `GITHUB_WEBHOOK_SECRET` needs to be the same on the server where this is deployed and set in GitHub.
2. Run `docker-compose build && docker-compose up -d`