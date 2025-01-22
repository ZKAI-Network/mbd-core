Contributing to mbd-core

## Release & Versioning

This project uses Git tags for versioning and maintains a custom index at https://ZKAI-Network.github.io/mbd-pypi-index that references each new tag.

### Prerequisites

1. Install Miniconda or Anaconda if you haven't already:
   - Download from [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)

2. Create and activate a Python 3.10 environment:
   ```bash
   # Create new environment
   conda create -n py310 python=3.10

   # Activate the environment
   conda activate py310
   ```

3. Install development dependencies:
   ```bash
   # From the project root
   make fix-lint  # This will install all dependencies including dev dependencies
   ```

   Note: Never modify requirements.txt directly. Instead:
   - Add production dependencies to requirements.in
   - Add development dependencies to appropriate files under requirements-dev/:
     - requirements-dev/lint.in: for linting tools
     - requirements-dev/docs.in: for documentation
     - requirements-dev/misc.in: for other development tools

### Development Workflow

1. Always ensure you're in the correct environment:
   ```bash
   conda activate py310
   ```

2. Before submitting a PR, run these commands in order:
   ```bash
   # Auto-fix lint errors, format code, and update requirements
   make fix-lint

   # Check for any remaining lint errors
   make lint

   # Run tests and get coverage report
   make test
   ```

   Note: If `make lint` shows errors that weren't auto-fixed, you'll need to fix them manually.

## Release & Versioning

This project uses Git tags for versioning and maintains a custom index at https://ZKAI-Network.github.io/mbd-pypi-index that references each new tag.

### Prerequisites

bump2version is included in the development dependencies and will be installed when running `make fix-lint`.

### Release Process

1. Ensure your PRs are merged into main branch

2. Make sure you're in the correct environment:
   ```bash
   conda activate py310
   ```

3. Update version using make targets:
   ```bash
   # For patch updates (0.0.x)
   make release-patch

   # For minor updates (0.x.0)
   make release-minor

   # For major updates (x.0.0)
   make release-major
   ```

4. Push the changes and tags:
   ```bash
   make release-tag
   ```

5. Update the mbd-pypi-index:
   - Go to the mbd-pypi-index repository
   - Switch to gh-pages branch
   - Edit index.html to add the new version:
     ```html
     <a href="git+https://github.com/ZKAI-Network/mbd-core.git@v{version}#egg=mbd_core-{version}+release" data-requires-python=">=3.10">mbd_core-{version}</a><br/>
     ```
   - Commit and push the changes to gh-pages branch

6. The new version can now be installed via:
   ```bash
   pip install mbd-core=={version} --extra-index-url https://ZKAI-Network.github.io/mbd-pypi-index
   ```

## Common Issues

If you encounter any issues with dependencies or versions, try the following:

1. Ensure you're in the correct environment:
   ```bash
   # Check current environment
   conda info --envs
   
   # Activate if needed
   conda activate py310
   ```

2. Verify Python version:
   ```bash
   python --version  # Should show Python 3.10.x
   ```

3. Clean and reinstall if needed:
   ```bash
   pip uninstall mbd-core
   pip install -e .
   ```

4. If you've added new dependencies:
   ```bash
   make fix-lint  # This will update and install all dependencies
   ```