# Denied Autonomous Commands

These commands must not be run automatically:

- git push
- Force-moving historical tags such as v0.1.0 or v0.1.1
- Deleting historical release directories such as releases/v0.1.0 or releases/v0.1.1
- Reading .env files, SSH keys, cloud credentials, or system secrets
- Production deployment
- Real production database migration
- Cloud resource creation or deletion
- Any command outside the project workspace unless explicitly approved by the user
