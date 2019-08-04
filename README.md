# pmake

A makefile generator using pure-python. This gives you full access to python functions, libraries, and variables, without a constrained DSL like cmake or bazel. Target dependency management is designed to be as explicit as possible (e.g. no global cmake compile options).

## Example

```sh
alias pmake='python builder.py'
pmake . # runs with make.py
make all
```

Example python makescript

```python
hello_project = project('hello')

hello = cpp.executable(project.name)
hello.set_standard(14)
if project.mode == 'release':
    hello.set_optimization_level(3)
hello.add_debug_symbols()
hello.add_options('-Wall -Werror')
hello.add_source('hello.cpp')

hello_project += hello
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
