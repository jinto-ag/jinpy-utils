# ADR-0001: Use MkDocs for Documentation

**Status:** ✅ Accepted
**Date:** 2025-08-12
**Authors:** Development Team

## Context

The project needed a comprehensive documentation system that could serve both human-readable guides and auto-generated API documentation. We had two potential approaches:

1. **Dual System**: MkDocs for rich documentation + GitHub Wiki for simple docs
2. **Single System**: MkDocs only as single source of truth

The dual system was causing maintenance overhead, content duplication, and inconsistencies.

## Decision

Use **MkDocs with Material theme** as the single source of truth for all documentation, replacing GitHub Wiki.

## Alternatives Considered

### Option 1: GitHub Wiki Only
- **Pros:** Simple, integrated with GitHub
- **Cons:** Limited theming, no API auto-generation, poor search, basic navigation
- **Why not chosen:** Insufficient for comprehensive technical documentation

### Option 2: Dual MkDocs + Wiki System
- **Pros:** Best of both worlds
- **Cons:** Maintenance overhead, content duplication, sync issues
- **Why not chosen:** Creates confusion and maintenance burden

### Option 3: Sphinx
- **Pros:** Powerful, Python-focused
- **Cons:** Complex configuration, steeper learning curve
- **Why not chosen:** MkDocs is simpler and sufficient for our needs

## Rationale

- **Single Source of Truth**: Eliminates duplication and inconsistencies
- **Professional Appearance**: Material theme provides modern, responsive design
- **API Integration**: mkdocstrings plugin auto-generates API docs from docstrings
- **Better UX**: Advanced search, navigation, mobile support
- **SEO Benefits**: Proper meta tags, sitemap generation
- **Developer Experience**: Simple markdown, easy to maintain

## Consequences

### Positive
- Professional documentation appearance
- Automated API documentation stays in sync with code
- Better search and navigation experience
- Single workflow for all documentation updates
- SEO optimized for better discoverability

### Negative
- GitHub Wiki becomes stale (acceptable trade-off)
- Requires GitHub Pages setup
- Slightly more complex than pure markdown

### Neutral
- Documentation hosted at GitHub Pages instead of wiki
- Build process required for changes

## Implementation

1. ✅ Configure MkDocs with Material theme
2. ✅ Set up mkdocstrings for API documentation
3. ✅ Create proper navigation structure following Diátaxis framework
4. ✅ Configure GitHub Actions for automated deployment
5. ✅ Disable wiki-sync workflow

## References

- [MkDocs](https://mkdocs.org) - Static site generator
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) - Theme documentation
- [Diátaxis](https://diataxis.fr/) - Documentation framework
- [mkdocstrings](https://mkdocstrings.github.io/) - API documentation plugin

---

*This ADR follows the [MADR](https://adr.github.io/madr/) format.*
