# Contributing to Stop Motion Homos

Thank you for your interest in contributing! This document provides guidelines for contributions.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**: `git clone https://github.com/yourusername/Stop-motion-homos.git`
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Install dev dependencies**: `pip install -r requirements.txt`
5. **Make your changes** and test thoroughly
6. **Commit with clear messages**: `git commit -m "Add descriptive message"`
7. **Push to your fork**: `git push origin feature/your-feature-name`
8. **Open a Pull Request** with a description of your changes

## Development Guidelines

### Code Style

- Use **PEP 8** style guidelines
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings for public methods

### Commit Messages

- Start with a verb: "Add", "Fix", "Refactor", "Improve"
- Be specific: `Fix A* cost barrier handling in mapper` not `Fix bug`
- Keep messages under 72 characters for subject lines

### Testing

Before submitting a PR:

1. Run the full pipeline: `python main.py`
2. Verify topological validation passes (✅ Checker)
3. Check for any performance regressions
4. Test with different manifold configurations if applicable

### Documentation

- Update README.md if adding user-facing features
- Add inline comments for complex algorithms
- Include docstrings for new classes and methods
- Explain the WHY, not just the WHAT

## Areas for Contribution

### High Priority

- **Visualization**: Tools to render loops in 3D space
- **Performance**: Optimize gradient descent or neighbor generation
- **Testing**: Add unit tests for core components
- **Documentation**: Mathematical background and examples

### Nice to Have

- Support for additional manifold types (Klein bottle, projective plane)
- GPU acceleration for large searches
- Web interface for interactive exploration
- Symbolic integration with SymPy

### Research Directions

- Time-dependent Lagrangians with periodic forcing
- Machine learning to predict geodesic classes
- Parallel batch processing on clusters
- Adaptive mesh refinement for dense exploration

## Bug Reports

When reporting bugs, include:

1. **Steps to reproduce** the issue
2. **Expected behavior** vs actual behavior
3. **Environment details** (Python version, OS, dependencies)
4. **Relevant output** or error messages
5. **Screenshots** if applicable

Example:
```
**Issue**: Topological checker fails on 4×4 torus

**Steps**:
1. Modify utils.py to create 4×4 torus
2. Run main.py

**Error**:
AssertionError at line 42 in main.py

**Environment**:
- Python 3.10
- NumPy 1.24.0
- NetworkX 3.0
```

## Feature Requests

Describe:

1. **Use case**: What problem does this solve?
2. **Implementation sketch**: How might it work?
3. **Impact**: Which components would need changes?
4. **Priority**: Is this blocking or nice-to-have?

## Review Process

Maintainers will review PRs within 1-2 weeks and may:

- Request changes for code quality or clarity
- Suggest optimizations or alternative approaches
- Ask for additional tests or documentation
- Approve and merge when satisfied

## Questions?

- Open a GitHub Issue for bugs or features
- Discuss ideas in Issues before implementing
- Check existing Issues to avoid duplicates

## Recognition

Contributors will be credited in:
- README.md (Contributors section)
- Commit history
- Release notes for major features

Thank you for making Stop Motion Homos better! 🎬
