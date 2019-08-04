# pmake

A makefile generator using pure-python. This gives you full access to python functions, libraries, and variables, without a constrained DSL like cmake or bazel. Target dependency management is designed to be as explicit as possible (e.g. no global cmake compile options).

See `make.py` for an example build script.

## Example

```sh
alias pmake='python builder.py'
pmake . # runs with make.py
make all
```

```sh
alias pmake='python builder.py'
pmake . --mode=release
make all
```

## Supported features

- project scoping
- c++ object files, executables, shared and static libraries
- custom compile options & defines
- compiler/c++ version config
- Easy functions for setting optimization level, adding debug symbols
- Pre/Post build shell functions
- Build modes (e.g. debug vs release)
- Cross-platform support (needs testing)
- Custom install path
- Build subdirectories
- Custom targets as shell functions

## TODO features

- Support build folders
- find_package
- Support for more languages
