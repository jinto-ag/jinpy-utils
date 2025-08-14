# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Architecture Decision Records (ADR) system following MADR format for documenting key decisions
- CHANGELOG.md following Keep a Changelog format with semantic versioning
- Professional MkDocs documentation with Material theme and responsive design
- Comprehensive API documentation using enhanced mkdocstrings configuration:
  - All public, protected, and private methods (including `__init__`, `__str__`, `__repr__`)
  - Complete type annotations, return types, args, and kwargs
  - Parameter details in table format with structured docstring sections
  - Source code links and inheritance information
- Decision tracking and navigation in documentation with dated entries (2025-12-18, 2025-12-19)

### Changed
- **BREAKING**: Logger configuration now uses `set_global_config()` for global settings instead of passing config to `get_logger()`
- Documentation moved from dual MkDocs/Wiki to MkDocs-only (single source of truth)
- GitHub Actions workflows simplified to use direct `uv run mkdocs` commands
- MkDocs theme upgraded to latest Material theme with comprehensive features
- API documentation enhanced to show maximum information following documentation standards
- mkdocstrings configuration optimized for comprehensive API display with table-style sections

### Removed
- GitHub Wiki synchronization (wiki-sync.yml workflow)
- Temporary documentation strategy and audit files
- Complex build scripts in favor of direct `uv run mkdocs` commands
- Unused MkDocs plugins that caused build issues

### Fixed
- Incorrect logger API usage patterns in documentation examples
- ConsoleBackendConfig parameter types (LogFormat enum vs string)
- All broken internal links in documentation
- MkDocs Material theme rendering issues with grid cards
- Documentation build warnings and duplicate file issues

### Security
- Updated GitHub Actions workflows to use latest action versions

## Historical Context

This project has been continuously evolving with structured logging, exception handling, and utility functions. The current release represents a major documentation overhaul and architectural clarification phase.

### Core Features (Existing)
- **Structured Logging**: Multi-backend logging system with JSON, console, file, REST API, and WebSocket support
- **Type-Safe Configuration**: Pydantic-based configuration management with environment variable integration
- **Exception Handling**: Centralized exception registry with structured error details
- **Utility Functions**: Time utilities and helper functions for common operations

---

## Versioning Strategy

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version when making incompatible API changes
- **MINOR** version when adding functionality in a backwards compatible manner
- **PATCH** version when making backwards compatible bug fixes

## Contributing

See [CONTRIBUTING.md](https://github.com/jinto-ag/jinpy-utils/blob/main/CONTRIBUTING.md) for contribution guidelines.

## Links

- **Documentation**: https://jinto-ag.github.io/jinpy-utils/
- **Repository**: https://github.com/jinto-ag/jinpy-utils/
- **Issues**: https://github.com/jinto-ag/jinpy-utils/issues
- **Releases**: https://github.com/jinto-ag/jinpy-utils/releases
