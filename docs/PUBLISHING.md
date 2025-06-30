# Publishing JSP to PyPI

This guide explains how to publish the `jsp` package to PyPI.

## Prerequisites

1. PyPI account: https://pypi.org/account/register/
2. (Optional) TestPyPI account: https://test.pypi.org/account/register/
3. API tokens generated for both accounts

## Setting Up Credentials

### Option 1: Environment Variables (Recommended)

Create a `.env` file in your local environment (never commit this!):

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual tokens
TWINE_USERNAME=__token__
TWINE_PASSWORD=pypi-YOUR_ACTUAL_TOKEN_HERE
```

Then source it before publishing:
```bash
source .env
```

### Option 2: .pypirc File

Create `~/.pypirc` in your home directory:

```bash
# Copy the example
cp .pypirc.example ~/.pypirc
chmod 600 ~/.pypirc

# Edit with your actual tokens
```

### Option 3: Keyring (Most Secure)

```bash
pip install keyring
keyring set https://upload.pypi.org/legacy/ __token__
# Enter your token when prompted
```

## Publishing Process

### 1. Test on TestPyPI First

```bash
# Run tests
make test

# Build and upload to TestPyPI
make upload-test

# Or use the script directly
python scripts/publish.py --test
```

Test the installation:
```bash
pip install -i https://test.pypi.org/simple/ jsp
```

### 2. Publish to PyPI

```bash
# Ensure version is updated in setup.py and pyproject.toml
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Build and upload to PyPI
make upload

# Or use the script directly
python scripts/publish.py
```

### 3. Verify Installation

```bash
pip install jsp
jsp --version
```

## Manual Publishing

If you prefer manual control:

```bash
# Install tools
pip install build twine

# Clean previous builds
make clean

# Build the package
python -m build

# Check the package
twine check dist/*

# Upload to TestPyPI
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Upload to PyPI
twine upload dist/*
```

## GitHub Actions

For automated publishing, the repository includes `.github/workflows/publish.yml`.

### Option 1: Trusted Publisher (Recommended)

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher with these settings:
   - **GitHub Repository Owner**: `jaredrummler` (your username)
   - **GitHub Repository Name**: `jsp`
   - **Workflow name**: `publish.yml`
   - **Environment name**: (leave blank)
3. The workflow will automatically publish on release creation

### Option 2: API Token

1. Add PyPI token as GitHub secret: `PYPI_API_TOKEN`
2. (Optional) Add TestPyPI token: `TEST_PYPI_API_TOKEN`
3. The workflow will use these tokens as a fallback

### Manual Trigger

You can manually trigger the workflow from GitHub Actions tab:
- Choose target: `testpypi` or `pypi`
- Click "Run workflow"

## Troubleshooting

### "Invalid or non-existent authentication"
- Ensure you're using `__token__` as username
- Check that your token starts with `pypi-`
- Verify token scope (project-specific vs account-wide)

### "Package exists"
- Increment version in `setup.py` and `pyproject.toml`
- Delete old builds: `make clean`

### "Invalid distribution"
- Run `twine check dist/*` to identify issues
- Ensure README.md exists and is valid
- Check that all required fields are in setup.py

## Version Management

Before publishing a new version:

1. Update version in `setup.py`
2. Update version in `pyproject.toml`  
3. Update CHANGELOG.md
4. Commit changes
5. Tag the release: `git tag -a v1.0.1 -m "Release version 1.0.1"`
6. Push tag: `git push origin v1.0.1`

## Security Notes

- Never commit `.env` or `.pypirc` files
- Use API tokens, not passwords
- Consider using project-scoped tokens
- Rotate tokens periodically
- Use keyring for local development