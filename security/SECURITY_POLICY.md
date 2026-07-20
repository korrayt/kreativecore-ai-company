# Security Policy

## Never commit secrets

Examples:

- GitHub personal access tokens
- API keys
- passwords
- signing certificates
- service-account files
- payment secrets
- license signing keys
- private customer or employee data

## If a secret is exposed

1. Revoke or rotate it immediately.
2. Check access and security logs.
3. Remove it from current files.
4. Assess whether Git history must be rewritten.
5. Record the incident privately.
6. Replace dependent credentials.
7. Verify the old credential no longer works.

Deleting a message or commit is not a substitute for revocation.

## Reporting

For public repositories, publish only a neutral security contact and supported-version policy.
Keep exploit details and private incident data outside public issues.
