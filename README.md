# MAS project



## Table of Contents
1. [Overview](#overview)
2. [Development](#development)
3. [Project Structure](#project-structure)
4. [Simulation Preview](#simulation-preview)
5. [Contributors](#contributors)

## Overview


## Development
This project follows the best practices we currently rely on for building maintainable Python projects. We use:

- **`uv`** for dependency management  
- **`pre-commit`** for automated code quality checks  
- **`Ruff`** for linting and formatting (a VS Code configuration is included)  
- **`Makefile`** to run common commands consistently

### Requirements
- **Python 3.12**
- **`uv`** (recommended) for dependency management and to automatically create the package link for a smoother development workflow
- **`make`** (recommended) to use the provided Makefile commands

### Environment setup
Install dependencies and set up `pre-commit` hooks:
```bash
make install
```

### Code quality
Run linting/formatting checks via `pre-commit`:
```bash
make pre-commit
```


## Project Structure
You'll find all the utility functions and classes (Python `.py` files) you'll need for our experiments and tests in the [`src`](./src/) folder. 


## Simulation Preview

## Contributors


|            Name            |                Email                  |
| :------------------------: | :-----------------------------------: |
|    MOLLY-MITTON Clément    |    clement.mollymitton@gmail.com      |
|       VERBECQ DIANE        |        diane.verbecq@gmail.com        |
