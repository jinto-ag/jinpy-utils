# API Documentation Standards

This document outlines the comprehensive API documentation standards implemented in jinpy-utils, following industry best practices for Python API documentation.

## Enhanced mkdocstrings Configuration

Our API documentation uses an enhanced mkdocstrings configuration that provides maximum information for developers:

### Global Configuration Features

```yaml
# mkdocs.yml - Enhanced mkdocstrings configuration
plugins:
  - mkdocstrings:
      default_handler: python
      handlers:
        python:
          options:
            # Comprehensive API display
            show_source: true
            show_signature_annotations: true
            separate_signature: true
            docstring_style: google

            # Show all methods and attributes
            show_root_heading: true
            show_root_toc_entry: true
            show_category_heading: true

            # Include comprehensive member information
            show_bases: true
            show_submodules: true
            signature_crossrefs: true

            # Enhanced documentation features
            docstring_section_style: table
            show_labels: true
            group_by_category: true
            show_if_no_docstring: true
            annotations_path: brief
            members_order: source
```

### What This Configuration Provides

#### 🔍 **Comprehensive Method Coverage**
- **Public methods**: All standard API methods
- **Protected methods**: `_protected_method()` methods for internal API understanding
- **Private methods**: `__private_method()` methods for complete API surface
- **Special methods**: `__init__`, `__str__`, `__repr__`, `__call__`, etc.
- **Magic methods**: `__enter__`, `__exit__`, `__iter__`, `__next__`, etc.

#### 📋 **Enhanced Information Display**
- **Type Annotations**: Complete parameter and return type information
- **Args & Kwargs**: Detailed parameter descriptions with types
- **Table Format**: Parameters displayed in organized, readable tables
- **Source Links**: Direct links to source code for each method
- **Inheritance**: Base class information and method resolution order
- **Signatures**: Separate, highlighted method signatures

#### 📖 **Professional Formatting**
- **Google Docstring Style**: Consistent, readable docstring parsing
- **Structured Sections**: Args, Returns, Raises, Examples in organized tables
- **Cross-References**: Automatic linking between related classes and methods
- **Category Grouping**: Methods organized by type (public, private, special)
- **TOC Integration**: Automatic table of contents generation

## API Reference Structure

### Standard Page Template

Each API reference page follows this enhanced template:

```markdown
# Module API Reference

Brief module description.

## Core Classes

### ClassName

::: module.ClassName
    options:
      show_root_heading: true
      show_root_toc_entry: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table
      members:
        - __init__
        - __new__
        - __str__
        - __repr__
        - public_method_1
        - public_method_2
        - _protected_method
        - __private_method
```

### Member Selection Strategy

We explicitly list important members to ensure comprehensive coverage:

#### Essential Methods Always Included:
- `__init__`: Constructor with all parameters
- `__new__`: Object creation (when relevant)
- `__str__`: String representation
- `__repr__`: Developer representation
- `__call__`: Callable behavior (when applicable)

#### Context-Specific Methods:
- **Container classes**: `__len__`, `__getitem__`, `__setitem__`, `__contains__`
- **Context managers**: `__enter__`, `__exit__`
- **Iterables**: `__iter__`, `__next__`
- **Comparison**: `__eq__`, `__hash__` (when relevant)

#### Internal Methods (When Informative):
- `_validate_*`: Validation methods that users might need to understand
- `_format_*`: Formatting methods that affect output
- `_create_*`: Factory methods that explain object creation

## Documentation Quality Standards

### 🎯 **Accuracy Requirements**
- **Source Verification**: All documented methods must exist in source code
- **Type Accuracy**: Parameter types must match actual implementation
- **Example Validation**: All code examples must be functional
- **Link Verification**: All internal links must resolve correctly

### 📝 **Content Standards**
- **Complete Parameter Information**: Every parameter documented with type and description
- **Return Value Documentation**: Clear description of return types and values
- **Exception Documentation**: All possible exceptions with conditions
- **Usage Examples**: Practical examples for complex methods

### 🎨 **Presentation Standards**
- **Table Format**: Parameters presented in organized tables
- **Syntax Highlighting**: Code examples with proper syntax highlighting
- **Cross-Linking**: Related classes and methods automatically linked
- **Mobile Responsive**: Documentation readable on all devices

## Implementation Examples

### Logger API Documentation

The Logger class demonstrates comprehensive API documentation:

```python
# Source: docs/reference/logger/core.md
::: jinpy_utils.logger.Logger
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      members:
        - __init__          # Constructor with all configuration options
        - __str__           # String representation showing logger name
        - __repr__          # Developer representation with full state
        - debug             # Debug level logging
        - info              # Info level logging
        - warning           # Warning level logging
        - error             # Error level logging
        - critical          # Critical level logging
        - _validate_level   # Internal validation for understanding
        - _format_message   # Internal formatting for advanced users
```

### Exception API Documentation

Exception classes show inheritance and comprehensive method coverage:

```python
# Source: docs/reference/base/exceptions.md
::: jinpy_utils.base.JPYBaseException
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table
      members:
        - __init__          # Constructor with error details
        - __str__           # User-friendly error message
        - __repr__          # Developer representation
        - __eq__            # Exception comparison
        - __hash__          # Hashing for sets/dicts
        - to_dict           # Serialization to dictionary
        - to_json           # JSON serialization
        - add_context       # Adding contextual information
        - _validate_error_code  # Internal validation
        - _serialize_details    # Internal serialization
```

## Maintenance Guidelines

### 📋 **Regular Reviews**
1. **Quarterly Source Audits**: Verify all documented methods still exist
2. **Type Annotation Updates**: Ensure type hints match current implementation
3. **Example Testing**: Validate all code examples work with current API
4. **Link Verification**: Check all cross-references resolve correctly

### 🔄 **Update Process**
1. **Code Changes**: Update documentation immediately when API changes
2. **New Methods**: Add to member lists with appropriate documentation
3. **Deprecated Methods**: Mark as deprecated before removal
4. **Breaking Changes**: Document in changelog with migration guide

### ✅ **Quality Checks**
- **Build Verification**: `uv run mkdocs build --clean` must pass
- **Link Testing**: All internal links must resolve
- **Example Validation**: All code examples must execute successfully
- **Type Consistency**: Parameter types must match implementation

## Performance Considerations

### ⚡ **Build Optimization**
- **Selective Member Lists**: Only include relevant methods to avoid bloat
- **Efficient Configuration**: Optimized mkdocstrings settings for speed
- **Clean Builds**: ~12-15 second full documentation builds

### 📊 **Size Management**
- **Essential Focus**: Prioritize most-used methods in member lists
- **Internal Method Selection**: Only include internal methods that aid understanding
- **Example Relevance**: Include examples that demonstrate real-world usage

## Integration with Development Workflow

### 🔗 **CI/CD Integration**
```yaml
# .github/workflows/docs.yml
- name: Build documentation
  run: uv run mkdocs build --strict

- name: Deploy to GitHub Pages
  run: uv run mkdocs gh-deploy --force
```

### 📝 **Documentation-First Development**
1. **New Features**: Document API before implementation
2. **Refactoring**: Update documentation alongside code changes
3. **Code Reviews**: Include documentation review in PR process
4. **Release Process**: Documentation updates are part of release checklist

---

This comprehensive API documentation system ensures developers have access to complete, accurate, and professionally presented API information, following industry best practices for Python library documentation.
