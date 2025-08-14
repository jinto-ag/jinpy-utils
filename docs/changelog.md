# Changelog

This page tracks all notable changes to jinpy-utils. For the complete changelog, see [CHANGELOG.md](https://github.com/jinto-ag/jinpy-utils/blob/main/CHANGELOG.md).

## Latest Changes

### Recent Improvements

#### Documentation System Overhaul ✨ (2025-12-19)
- **Single Source of Truth**: Moved to MkDocs-only documentation (eliminated wiki duplication)
- **Professional Theme**: Upgraded to latest Material for MkDocs with modern, responsive design
- **Comprehensive API Documentation**: Enhanced mkdocstrings with complete information:
  - All public, protected, and private methods (including `__init__`, `__str__`, `__repr__`)
  - Complete type annotations, return types, args, and kwargs displayed properly
  - Parameter details in professional table format
  - Source code links and inheritance information
- **Architecture Decision Records**: Professional ADR system following industry MADR format
- **Professional Standards**: Following OSS best practices for documentation and decision tracking

#### API Improvements 🔧 (2025-12-18/19)
- **Breaking Change**: Logger configuration now uses `set_global_config()` for global settings
- **Type Safety**: Fixed configuration parameter types (LogFormat enum vs strings)
- **Accurate Examples**: All documentation examples verified against actual API implementations
- **Enhanced Display**: Table-style parameter documentation with comprehensive type information

#### Developer Experience 🚀 (2025-12-19)
- **Simplified Tooling**: Direct `uv run mkdocs serve` and `uv run mkdocs build` commands
- **Fast Professional Builds**: ~14 second comprehensive documentation builds
- **Industry Standards**: Clean configuration following documentation best practices
- **Decision Traceability**: All architectural decisions documented with full context

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| **Unreleased** | 2025-12-19 | Comprehensive documentation overhaul, enhanced API docs, ADR system, breaking config changes |
| **Historical** | Various | Core logging, exceptions, utilities implementation |

## What's Next?

- 📋 Formal versioning and releases
- 🏷️ Semantic version tagging
- 📦 PyPI publishing automation
- 🔄 Continuous integration improvements

## Full Changelog

For detailed change history with technical specifics, see the complete [CHANGELOG.md](https://github.com/jinto-ag/jinpy-utils/blob/main/CHANGELOG.md) file.

## Contributing

Found a bug or have a suggestion?

- 🐛 **Report Issues**: [GitHub Issues](https://github.com/jinto-ag/jinpy-utils/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/jinto-ag/jinpy-utils/discussions)
- 🔧 **Contribute Code**: See [Contributing Guidelines](https://github.com/jinto-ag/jinpy-utils/blob/main/CONTRIBUTING.md)
