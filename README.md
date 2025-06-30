# JSP: Joseph Smith Papers CLI Tool

A command-line tool for Mormon enthusiasts and scholars to enhance their experience using the [Joseph Smith Papers](https://www.josephsmithpapers.org/) project.

---

## ✨ Features

* **High-quality Image Retrieval**: Easily download and stitch high-resolution images from Joseph Smith Papers' OpenSeadragon viewer at maximum quality (JPEG quality 100 by default).
* **Content Scraping**: Extract webpage content into Markdown format for textual analysis, research, and AI integrations.

## 📌 Use Cases

* **Historians**: Access high-fidelity images of original documents for scholarly publications.
* **LDS Members**: View high-resolution images of historical items such as the Book of Abraham facsimiles.
* **Researchers**: Download structured textual data from Joseph Smith Papers for detailed textual analysis, research, or AI-assisted analysis.

---

## 🚀 Installation

### Using pip (Recommended)

```bash
pip install jsp
```

### Manual Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/jsp.git
cd jsp
```

Run the install script (macOS/Linux):

```bash
./install.sh
```

For Windows users, manual installation instructions will be provided soon.

---

## ⚙️ Usage

### Default command (runs all available tasks)

```bash
jsp process <URL>
```

### Individual commands

#### Download and stitch high-quality image:

```bash
jsp download-image <URL>
```

#### Scrape webpage content to Markdown:

```bash
jsp scrape-content <URL>
```

### Command Options

```bash
# Specify output directory
jsp <URL> -o /path/to/output

# Set JPEG quality (1-100, default: 100)
jsp <URL> --quality 95

# Disable browser automation for faster scraping
jsp <URL> --no-browser

# Enable verbose output
jsp <URL> -v

# Preview actions without executing
jsp <URL> --dry-run
```

### Output

By default, outputs will be placed in the following directory:

```
output/{url-path}/
├── image.jpg
└── content.md
```

Use the `-o` or `--output` option to specify a custom output directory.

---

## 🛠 Requirements

* **Python**: Version 3.9 or later recommended
* **Operating Systems**: macOS prioritized; Windows compatibility intended but not yet fully tested.

---

## 🤝 Contributing

Contributions are welcome! Please read our [contributing guide](CONTRIBUTING.md) and submit pull requests to our repository.

---

## 🤖 Agent Guidelines

For guidance on using AI-driven coding assistants, see:

- [AGENTS.md](AGENTS.md) for OpenAI-powered agents (Codex CLI / ChatGPT).
- [CLAUDE.md](CLAUDE.md) for Anthropic’s Claude agent.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🐞 Issues & Feedback

Please submit any issues, bugs, or feature requests through [GitHub Issues](https://github.com/yourusername/jsp/issues).

---

*This project is actively under development.*
