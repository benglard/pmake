# pmake

Generate cmake files from python. Use conan to install dependencies.

## Example

```sh
pip install -e .
```

Example python makescript

```python
from pmake import project, fetch_contents
import pmake.cpp as cpp

hello_project = project('hello')
hello_project.compiler(cpp='g++', c='gcc')
hello_project.requires('nlohmann_json', version='3.11.2')

hello = cpp.executable(f'{hello_project.name}.out')
hello.options('-Wall -Werror')
hello.sources('hello.cpp')
hello.includes('/usr/include')
hello.defines('TEST')
hello.library_paths('/usr/lib')
hello_project += hello
```

```sh
python make.py --mode=release
```