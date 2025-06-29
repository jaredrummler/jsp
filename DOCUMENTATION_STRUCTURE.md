# JSP Documentation Structure

The project documentation has been reorganized for better accessibility and maintenance. This document explains the new structure and where to find different types of information.

## 📚 Main Documentation (`/docs/`)

All project documentation is now organized under the `/docs/` directory with the following structure:

```
docs/
├── README.md                    # Documentation index and navigation guide
├── planning/                    # Planning documents and roadmaps
│   ├── CONTENT_SCRAPER_PLAN.md # Detailed plan for content scraper module
│   ├── TODO.md                 # Project-wide task tracking
│   └── AGENTS.md               # Guidelines for AI coding assistants
├── architecture/               # Technical architecture and design
│   ├── ARCHITECTURE.md         # Overall system architecture
│   ├── SCRAPER_ARCHITECTURE.md # Content scraper architecture with diagrams
│   ├── IMPLEMENTATION_GUIDE.md # Step-by-step implementation guide
│   └── IMPLEMENTATION_STATUS.md # Current implementation progress
├── implementation/             # Implementation details (to be populated)
├── reference/                  # Reference materials
│   └── jsp_website_patterns.md # HTML/CSS patterns on JSP website
└── examples/                   # Usage examples
    └── cli_usage.md           # CLI command examples and workflows
```

## 🛠️ Development Resources (`/.dev/`)

Development tools and experimental code are organized under `/.dev/`:

```
.dev/
├── README.md                   # Guide for using development tools
├── scripts/                    # Utility scripts for development
│   └── extract_jsp_content_sections.py  # Prototype content extractor
├── fixtures/                   # Test data and HTML samples
└── sandbox/                    # Experimental code playground
```

## 🔍 Quick Reference

### For Implementers
- Start here: `/docs/architecture/IMPLEMENTATION_GUIDE.md`
- Current status: `/docs/architecture/IMPLEMENTATION_STATUS.md`
- Scraper plan: `/docs/planning/CONTENT_SCRAPER_PLAN.md`

### For AI Assistants
- Project rules: `/CLAUDE.md`
- AI guidelines: `/docs/planning/AGENTS.md`
- Tasks: `/docs/planning/TODO.md`

### For Testing
- Development scripts: `/.dev/scripts/`
- Test fixtures: `/.dev/fixtures/`
- Examples: `/docs/examples/`

### For Reference
- JSP patterns: `/docs/reference/jsp_website_patterns.md`
- Architecture: `/docs/architecture/SCRAPER_ARCHITECTURE.md`
- CLI usage: `/docs/examples/cli_usage.md`

## 📝 Documentation Standards

1. **Keep docs up-to-date** - Update documentation when code changes
2. **Use clear structure** - Follow the established directory organization
3. **Link between docs** - Use relative links to connect related documents
4. **Include examples** - Provide code examples and usage scenarios
5. **Document decisions** - Explain why, not just what

## 🚀 Getting Started

1. Review the main documentation index: `/docs/README.md`
2. Check implementation status: `/docs/architecture/IMPLEMENTATION_STATUS.md`
3. Read the appropriate planning docs for your task
4. Use development tools in `/.dev/` for experimentation
5. Follow the patterns documented in `/docs/reference/`

Last Updated: 2024-06-29