# Security Policy

## Supported Versions

We support the latest minor of the `jinpy-utils` package. Older minors may receive critical security fixes at our discretion.

## Reporting a Vulnerability

- Please report security issues via GitHub Security Advisories or by emailing `project.jintoag@gmail.com`.
- Do not open public issues for security reports.
- We will acknowledge reports within 72 hours and provide a timeline for a fix where possible.

## Disclosure Policy

- We follow responsible disclosure. We will coordinate a fix and publish a security release.
- Credits will be given to reporters who request it.

## Best Practices

- Keep dependencies up to date (Dependabot enabled).
- CI runs static analysis (ruff, mypy) and tests on every PR.
- Tokens and secrets must be stored in GitHub Secrets.
