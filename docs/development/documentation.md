# Documentation Development

This guide covers how to contribute to and maintain the jinpy-utils documentation.

## Overview

jinpy-utils uses [MkDocs](https://www.mkdocs.org/) with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme to generate comprehensive documentation that includes:

- **Manual documentation** - Written in Markdown
- **API documentation** - Automatically generated from source code
- **Interactive examples** - Code snippets with syntax highlighting
- **Multi-version support** - Version-aware documentation
- **Search functionality** - Full-text search across all content

## Documentation Structure

Our documentation follows the [Diátaxis](https://diataxis.fr/) framework:

```
docs/
├── index.md                    # Home page
├── getting-started/           # Tutorials (learning-oriented)
│   ├── installation.md
│   ├── quick-start.md
│   └── configuration.md
├── guides/                    # How-to guides (problem-oriented)
│   ├── logger/
│   ├── base-exceptions/
│   └── utils/
├── reference/                 # API reference (information-oriented)
│   ├── index.md
│   ├── logger/
│   ├── base/
│   └── utils/
├── development/              # Development guides
│   ├── contributing.md
│   ├── setup.md
│   └── documentation.md     # This file
└── assets/                   # Static assets
    ├── stylesheets/
    ├── javascripts/
    └── images/
```

### Content Types

#### Tutorials (Getting Started)
- **Purpose**: Learning-oriented, step-by-step guidance
- **Audience**: New users who want to learn
- **Structure**: Sequential, building complexity gradually
- **Style**: Friendly, encouraging, practical

#### Guides (User Guide)
- **Purpose**: Problem-oriented, specific solutions
- **Audience**: Users who know what they want to achieve
- **Structure**: Goal-focused, task-oriented
- **Style**: Direct, actionable, comprehensive

#### Reference (API Reference)
- **Purpose**: Information-oriented, comprehensive details
- **Audience**: Users who need precise information
- **Structure**: Systematic, complete, consistent
- **Style**: Factual, accurate, cross-linked

#### Explanations (Development)
- **Purpose**: Understanding-oriented, background and context
- **Audience**: Users who want to understand why and how
- **Structure**: Topic-based, interconnected concepts
- **Style**: Thoughtful, balanced, clarifying

## Local Development

### Prerequisites

Ensure you have the required dependencies:

```bash
# Install project with documentation dependencies
pip install -e .[dev]

# Or install documentation dependencies only
pip install mkdocs mkdocs-material mkdocstrings[python]
```

### Quick Start

Start the development server:

```bash
# Using make (recommended)
make docs-serve

# Or using the build script
python scripts/build-docs.py serve

# Or directly with mkdocs
mkdocs serve
```

The documentation will be available at http://localhost:8000 with live reload.

### Available Commands

We provide several convenient commands for documentation development:

```bash
# Development
make docs-serve          # Start development server
make docs-build          # Build production documentation
make docs-validate       # Validate links and structure

# Maintenance
make docs-clean          # Clean build artifacts
make docs-optimize       # Optimize images and assets
make docs-stats          # Show documentation statistics

# Advanced
make docs-pdf            # Generate PDF documentation
make docs-versions       # Build multi-version documentation
make docs-all            # Complete build pipeline
```

See `make docs-help` for a complete list of available commands.

## Writing Documentation

### Markdown Guidelines

We use extended Markdown with additional features:

#### Basic Formatting

```markdown
# Main heading (H1) - only one per page
## Section heading (H2)
### Subsection heading (H3)

**Bold text** for emphasis
*Italic text* for subtle emphasis
`code` for inline code references
```

#### Code Blocks

Use fenced code blocks with language specification:

```markdown
```python title="example.py"
from jinpy_utils.logger import get_logger

logger = get_logger("example")
logger.info("Hello, world!")
```
```

#### Admonitions

Use admonitions for important information:

```markdown
!!! info "Information"
    This is general information that users should know.

!!! warning "Warning"
    This is something users should be careful about.

!!! danger "Danger"
    This is something that could cause serious problems.

!!! tip "Pro Tip"
    This is a helpful tip for advanced users.

!!! example "Example"
    This shows a practical example.
```

#### Tabs

Group related information with tabs:

```markdown
=== "Python"

    ```python
    from jinpy_utils.logger import get_logger
    logger = get_logger("app")
    ```

=== "Configuration"

    ```yaml
    logger:
      level: INFO
      backends:
        - type: console
    ```
```

#### Links and Cross-References

```markdown
# Internal links
[Installation Guide](installation.md)
[API Reference](../reference/logger/core.md)

# External links
[MkDocs Documentation](https://www.mkdocs.org/)

# Cross-references with anchors
[Logger Configuration](#logger-configuration)
```

### API Documentation

API documentation is automatically generated from source code using [mkdocstrings](https://mkdocstrings.github.io/):

```markdown
# Include complete module documentation
::: jinpy_utils.logger.get_logger
    options:
      show_source: true
      show_signature_annotations: true

# Include specific class members
::: jinpy_utils.logger.Logger
    options:
      members:
        - __init__
        - info
        - error
        - debug
```

### Documentation Standards

#### Writing Style

- **Clear and concise**: Use simple, direct language
- **Active voice**: "Configure the logger" vs "The logger should be configured"
- **Present tense**: "The function returns" vs "The function will return"
- **User-focused**: Address the reader as "you"
- **Consistent terminology**: Use the same terms throughout

#### Code Examples

- **Complete and runnable**: Examples should work when copy-pasted
- **Realistic**: Use practical, real-world scenarios
- **Well-commented**: Explain non-obvious parts
- **Error handling**: Show proper error handling patterns
- **Import statements**: Always include necessary imports

```python
# Good example - complete and realistic
from jinpy_utils.logger import get_logger, create_production_config
from jinpy_utils.base import JPYConfigurationError

try:
    # Configure for production use
    config = create_production_config()
    logger = get_logger("payment_service", config)

    # Process payment with structured logging
    logger.info("Processing payment",
               user_id=123,
               amount=99.99,
               currency="USD")

except JPYConfigurationError as e:
    print(f"Configuration error: {e.message}")
    # Handle configuration error appropriately
```

#### Screenshots and Images

- **High quality**: Use high-resolution images
- **Consistent style**: Maintain visual consistency
- **Alt text**: Always include descriptive alt text
- **Optimization**: Optimize images for web (use `make docs-optimize`)

```markdown
![Logger output example](../assets/images/logger-output.png "Example of structured logger output")
```

## Advanced Features

### Multi-Version Documentation

We support multiple versions of documentation using [mike](https://github.com/jimporter/mike):

```bash
# Deploy specific version
mike deploy v1.0.0 latest --update-aliases

# Set default version
mike set-default latest

# List all versions
mike list
```

### Custom Styling

Custom CSS is located in `docs/assets/stylesheets/custom.css`:

```css
/* Brand colors */
:root {
  --md-primary-fg-color: #1976d2;
  --md-accent-fg-color: #2196f3;
}

/* Custom components */
.api-reference {
  border-left: 4px solid var(--md-primary-fg-color);
  padding-left: 1rem;
}
```

### Custom JavaScript

Interactive features are in `docs/assets/javascripts/custom.js`:

```javascript
// Add copy feedback to code blocks
function addCopyFeedback() {
    const copyButtons = document.querySelectorAll('[data-clipboard-target]');
    // Implementation details...
}
```

### Search Configuration

Search is configured in `mkdocs.yml`:

```yaml
plugins:
  - search:
      separator: '[\s\u200b\-_,:!=\[\]()"`/]+|\.(?!\d)|&[lg]t;|(?!\b)(?=[A-Z][a-z])'
```

## Content Guidelines

### Writing Tutorials

Tutorials should be learning-oriented and take users through a complete journey:

1. **Clear objective**: State what the user will learn
2. **Prerequisites**: List what users need to know/have
3. **Step-by-step**: Break down into manageable steps
4. **Verification**: Help users confirm they're on track
5. **Next steps**: Point to related content

### Writing Guides

How-to guides should be problem-oriented and solution-focused:

1. **Problem statement**: Clearly define the problem
2. **Solution overview**: Brief overview of the approach
3. **Detailed steps**: Specific implementation details
4. **Variations**: Alternative approaches or configurations
5. **Troubleshooting**: Common issues and solutions

### Writing Reference

API reference should be comprehensive and systematic:

1. **Consistent structure**: Same format for all items
2. **Complete information**: All parameters, return values, exceptions
3. **Type information**: Precise type annotations
4. **Examples**: Practical usage examples
5. **Cross-references**: Links to related functionality

## Quality Assurance

### Automated Checks

Our CI/CD pipeline automatically:

- **Validates markdown syntax**: Checks for syntax errors
- **Verifies links**: Validates internal and external links
- **Builds documentation**: Ensures successful builds
- **Optimizes assets**: Compresses images and minifies CSS/JS
- **Checks HTML output**: Validates generated HTML

### Manual Review Process

1. **Content review**: Verify accuracy and completeness
2. **Style review**: Check adherence to style guidelines
3. **Link testing**: Manually test critical links
4. **Cross-browser testing**: Test on different browsers
5. **Mobile testing**: Ensure mobile responsiveness

### Performance Considerations

- **Image optimization**: Use `make docs-optimize`
- **Minimize dependencies**: Only include necessary plugins
- **Efficient search**: Configure search for optimal performance
- **CDN usage**: Use CDNs for external resources

## Troubleshooting

### Common Issues

#### Build Failures

```bash
# Check for syntax errors
mkdocs build --strict

# Debug specific issues
mkdocs build --verbose
```

#### Link Validation Failures

```bash
# Check specific links
markdown-link-check docs/path/to/file.md

# Skip external links
markdown-link-check --config .github/markdown-link-check.json
```

#### Plugin Issues

```bash
# Clear plugin cache
rm -rf .mkdocs_cache/

# Reinstall plugins
pip install --upgrade --force-reinstall mkdocs-material mkdocstrings
```

### Development Tips

1. **Use live reload**: The development server automatically reloads on changes
2. **Check browser console**: Look for JavaScript errors
3. **Validate early**: Run `make docs-validate` frequently
4. **Test on mobile**: Use browser developer tools
5. **Monitor performance**: Check page load times

## Contributing to Documentation

### Getting Started

1. **Fork the repository**: Create your own fork on GitHub
2. **Clone locally**: Clone your fork to your development machine
3. **Install dependencies**: Run `pip install -e .[dev]`
4. **Start development server**: Run `make docs-serve`
5. **Make changes**: Edit documentation files
6. **Test thoroughly**: Validate your changes work correctly
7. **Submit PR**: Create a pull request with your changes

### PR Guidelines

- **Clear title**: Describe what your PR changes
- **Detailed description**: Explain why the change is needed
- **Test your changes**: Ensure all checks pass
- **Follow style guide**: Adhere to our writing standards
- **Update related docs**: Keep cross-references current

### Review Process

1. **Automated checks**: CI pipeline validates changes
2. **Peer review**: Team members review content and code
3. **Final approval**: Maintainer approves and merges
4. **Deployment**: Changes automatically deploy to live site

## Resources

### Documentation Tools

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [mike (versioning)](https://github.com/jimporter/mike)

### Writing Resources

- [Diátaxis Documentation Framework](https://diataxis.fr/)
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Write the Docs](https://www.writethedocs.org/)

### Markdown Resources

- [Markdown Guide](https://www.markdownguide.org/)
- [Material for MkDocs Reference](https://squidfunk.github.io/mkdocs-material/reference/)
- [Python-Markdown Extensions](https://python-markdown.github.io/extensions/)

## Questions?

If you have questions about documentation:

1. **Check this guide**: Most common questions are covered here
2. **Search existing docs**: Use the search functionality
3. **Check GitHub issues**: Look for related discussions
4. **Ask in discussions**: Use GitHub Discussions for questions
5. **Contact maintainers**: Reach out to the core team
