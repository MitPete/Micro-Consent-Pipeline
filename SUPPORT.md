# Support

Welcome to the Micro-Consent-Pipeline project! This document provides information on how to get help, report issues, and contribute to the project.

## Getting Help

### 📚 Documentation

Before asking for help, please check our documentation:

- **[README](README.md)** - Project overview and quick start
- **[Installation Guide](INSTALLATION.md)** - Detailed setup instructions
- **[API Documentation](https://api.micro-consent-pipeline.example.com/docs)** - Interactive API docs
- **[Release Notes](RELEASE_NOTES.md)** - Release information and procedures
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment instructions

### 💬 Community Support

- **[GitHub Discussions](https://github.com/MitPete/Micro-Consent-Pipeline/discussions)** - Ask questions, share ideas, and get help from the community
- **[Stack Overflow](https://stackoverflow.com/questions/tagged/micro-consent-pipeline)** - Ask technical questions with the `micro-consent-pipeline` tag

### 🐛 Reporting Issues

Found a bug? Please help us improve by reporting it:

1. **Search existing issues** first to avoid duplicates
2. **Use our issue templates** for better problem descriptions
3. **Provide detailed information** to help us reproduce the issue

[**Create a Bug Report →**](https://github.com/MitPete/Micro-Consent-Pipeline/issues/new?template=bug_report.md)

### 💡 Feature Requests

Have an idea for a new feature?

1. **Check existing feature requests** to see if it's already been suggested
2. **Start a discussion** in [GitHub Discussions](https://github.com/MitPete/Micro-Consent-Pipeline/discussions) to gather feedback
3. **Create a feature request** if there's community interest

[**Request a Feature →**](https://github.com/MitPete/Micro-Consent-Pipeline/issues/new?template=feature_request.md)

## Issue Guidelines

### Before Creating an Issue

- [ ] Search existing issues and discussions
- [ ] Check the latest documentation
- [ ] Verify you're using a supported version
- [ ] Try to reproduce the issue with minimal steps

### Bug Reports Should Include

- **Environment details**: OS, Python version, package versions
- **Steps to reproduce**: Clear, numbered steps
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Error messages**: Full error messages and stack traces
- **Code samples**: Minimal code that reproduces the issue
- **Screenshots**: If applicable, especially for UI issues

### Feature Requests Should Include

- **Use case**: Why do you need this feature?
- **Proposed solution**: How would you like it to work?
- **Alternatives considered**: What other solutions have you considered?
- **Additional context**: Any other relevant information

## Contributing

We welcome contributions from everyone! Here's how you can help:

### 🚀 Quick Contributions

- **Fix typos** in documentation
- **Improve error messages** for better user experience
- **Add examples** to documentation
- **Write tests** for existing functionality
- **Report bugs** you encounter

### 🧭 Getting Started

1. **Read our [Contributing Guide](CONTRIBUTING.md)** for detailed instructions
2. **Review our [Code of Conduct](CODE_OF_CONDUCT.md)**
3. **Browse [Good First Issues](https://github.com/MitPete/Micro-Consent-Pipeline/labels/good%20first%20issue)**
4. **Join the conversation** in GitHub Discussions

### 📋 Contribution Process

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following our coding standards
4. **Write or update tests** for your changes
5. **Update documentation** if needed
6. **Commit your changes** using [Conventional Commits](https://www.conventionalcommits.org/)
7. **Push to your fork** (`git push origin feature/amazing-feature`)
8. **Create a Pull Request** with a clear description

### 🧪 Testing Expectations

All contributions should include appropriate tests:

- **Unit tests** for new functions and classes
- **Integration tests** for API endpoints
- **Documentation tests** for examples in docs
- **Performance tests** for optimization changes

Run tests locally:

```bash
pytest -v
pytest --cov=micro_consent_pipeline
```

### 📝 Documentation Contributions

Documentation improvements are always welcome:

- **API documentation** improvements
- **Tutorial writing** for common use cases
- **Example applications** showing real-world usage
- **Translation** to other languages
- **Video tutorials** and guides

## Branching Strategy

### Branch Types

- **`main`** - Production-ready code, protected branch
- **`develop`** - Integration branch for features (if used)
- **`feature/*`** - New features (`feature/add-oauth-support`)
- **`fix/*`** - Bug fixes (`fix/memory-leak-parser`)
- **`docs/*`** - Documentation changes (`docs/api-examples`)
- **`chore/*`** - Maintenance tasks (`chore/update-dependencies`)

### Pull Request Process

1. **Target the correct branch** (usually `main`)
2. **Use descriptive titles** following conventional commits
3. **Fill out the PR template** completely
4. **Ensure CI passes** (all tests, linting, security checks)
5. **Request review** from maintainers
6. **Address feedback** promptly and thoughtfully
7. **Squash commits** if requested by maintainers

### Review Process

- **Initial review** within 48 hours (goal)
- **Feedback** provided constructively and clearly
- **Approval required** from at least one maintainer
- **Automated checks** must pass (CI, security, formatting)

## Supported Versions

We support the following versions:

| Version | Status  | Python | Support Level       |
| ------- | ------- | ------ | ------------------- |
| 1.x.x   | Current | 3.10+  | Full support        |
| 0.x.x   | Legacy  | 3.8+   | Security fixes only |

### Security Updates

- **Critical vulnerabilities**: Patched immediately
- **High severity**: Patched within 48 hours
- **Medium/Low severity**: Included in next regular release

Report security vulnerabilities privately to: security@micro-consent-pipeline.example.com

## Response Times

### Issues and Bug Reports

- **Initial response**: Within 48 hours
- **Critical bugs**: Within 24 hours
- **Feature requests**: Within 1 week for initial feedback

### Pull Requests

- **Initial review**: Within 48 hours
- **Follow-up reviews**: Within 24 hours after updates

### Discussions

- **Community questions**: Best effort by community
- **Design discussions**: Maintainer input within 1 week

_Note: These are goals, not guarantees. Response times may vary based on maintainer availability and issue complexity._

## Repository Secrets (CI / Release)

For CI jobs that build and publish container images or push artifacts, please ensure the following repository secrets are configured in GitHub (Settings → Secrets → Actions):

- `DOCKERHUB_USERNAME` — Docker Hub username (if using Docker Hub)
- `DOCKERHUB_TOKEN` — Docker Hub access token/password (keep this secret)
- `GITHUB_TOKEN` — Provided automatically by Actions but may need additional permissions for external registries

If you use GitHub Packages instead of Docker Hub, you can rely on the default `GITHUB_TOKEN` and adjust the workflows accordingly. Keep these secrets up-to-date and restricted to maintainers only.

## Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Be Helpful

- Answer questions when you can
- Share your knowledge and experience
- Help newcomers get started
- Provide constructive feedback

### Be Patient

- Remember that maintainers are volunteers
- Understand that complex issues take time to resolve
- Be patient with community members learning
- Give people time to respond

## Resources

### Development Environment

- **[Development Setup](docs/development.md)** - Set up your dev environment
- **[Testing Guide](docs/testing.md)** - How to run and write tests
- **[API Reference](docs/api.md)** - Complete API documentation

### Community

- **[Discussions](https://github.com/MitPete/Micro-Consent-Pipeline/discussions)** - Community forum
- **[Contributors](CONTRIBUTORS.md)** - Meet the team
- **[Changelog](CHANGELOG.md)** - What's new in each release

### Project Management

- **[Roadmap](https://github.com/MitPete/Micro-Consent-Pipeline/projects)** - Future plans
- **[Milestones](https://github.com/MitPete/Micro-Consent-Pipeline/milestones)** - Release planning
- **[Labels](https://github.com/MitPete/Micro-Consent-Pipeline/labels)** - Issue categorization

## Contact

### General Questions

- GitHub Discussions: https://github.com/MitPete/Micro-Consent-Pipeline/discussions
- Email: peter.mitchell@example.com

### Security Issues

- Email: security@micro-consent-pipeline.example.com
- See [SECURITY.md](SECURITY.md) for details

### Business Inquiries

- Email: business@micro-consent-pipeline.example.com

---

Thank you for your interest in contributing to Micro-Consent-Pipeline! 🎉

_Last updated: 2025-10-21_
