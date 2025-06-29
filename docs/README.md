# JSP Project Documentation

This directory contains all documentation for the Joseph Smith Papers (JSP) command-line tool project.

## Directory Structure

### 📁 [planning/](planning/)
Planning documents and roadmaps for features and development.

- **[CONTENT_SCRAPER_PLAN.md](planning/CONTENT_SCRAPER_PLAN.md)** - Comprehensive plan for implementing the content scraper module
- **[TODO.md](planning/TODO.md)** - Project-wide task tracking and TODO items
- **[AGENTS.md](../AGENTS.md)** - Guidelines for AI coding assistants

### 📁 [architecture/](architecture/)
Technical architecture and implementation details.

- **[ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - Overall system architecture
- **[SCRAPER_ARCHITECTURE.md](architecture/SCRAPER_ARCHITECTURE.md)** - Content scraper module architecture with data flow diagrams
- **[IMPLEMENTATION_GUIDE.md](architecture/IMPLEMENTATION_GUIDE.md)** - Step-by-step implementation guide
- **[IMPLEMENTATION_STATUS.md](architecture/IMPLEMENTATION_STATUS.md)** - Current implementation status and progress

### 📁 [implementation/](implementation/)
Implementation-specific documentation and code examples.

*Currently empty - will contain:*
- Module-specific implementation details
- Code style guides
- Design decisions and rationale

### 📁 [reference/](reference/)
Reference materials and external resources.

*Currently empty - will contain:*
- JSP website structure documentation
- OpenSeadragon API reference
- HTML/CSS patterns found on JSP
- Test data and fixtures

### 📁 [examples/](examples/)
Example usage and sample outputs.

*Currently empty - will contain:*
- Example CLI commands
- Sample extracted content
- Configuration examples
- Integration examples

## Quick Links

### For Developers
1. Start with [ARCHITECTURE.md](architecture/ARCHITECTURE.md) for system overview
2. Review [IMPLEMENTATION_GUIDE.md](architecture/IMPLEMENTATION_GUIDE.md) for development workflow
3. Check [IMPLEMENTATION_STATUS.md](architecture/IMPLEMENTATION_STATUS.md) for current progress

### For AI Assistants
1. Read [AGENTS.md](../AGENTS.md) for collaboration guidelines
2. Review [CLAUDE.md](../CLAUDE.md) for project-specific instructions
3. Check [TODO.md](planning/TODO.md) for pending tasks

### For Contributors
1. See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
2. Review code style in implementation guides
3. Check open issues on GitHub

## Documentation Standards

### File Naming
- Use UPPERCASE for top-level documentation (e.g., `README.md`, `ARCHITECTURE.md`)
- Use lowercase with underscores for sub-documents (e.g., `content_scraper_details.md`)
- Include dates in design documents (e.g., `design_decision_2024_06_29.md`)

### Content Guidelines
- Use clear headings and subheadings
- Include diagrams where helpful (ASCII or Mermaid)
- Provide code examples for technical concepts
- Keep documentation up-to-date with implementation

### Markdown Standards
- Use ATX-style headers (`#`, `##`, etc.)
- Use fenced code blocks with language hints
- Use relative links for internal references
- Include table of contents for long documents

## Maintenance

This documentation should be updated whenever:
- New features are planned or implemented
- Architecture decisions are made or changed
- Implementation details change significantly
- New reference materials are discovered

Last Updated: 2024-06-29
