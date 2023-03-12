import os
import os.path
from platform import system

OS = system()
if OS == 'Windows':
    url = 'https://download.pytorch.org/libtorch/cu116/libtorch-win-shared-with-deps-1.13.1%2Bcu116.zip'
elif OS == 'Linux':
    url = 'https://download.pytorch.org/libtorch/cu116/libtorch-cxx11-abi-shared-with-deps-1.13.1%2Bcu116.zip'
elif OS == 'Darwin':
    url = 'https://download.pytorch.org/libtorch/cpu/libtorch-macos-1.13.1.zip'
if not os.path.exists('libtorch'):
    print('Downloading libtorch...')
    download(url, 'libtorch.zip')
    unzip('libtorch.zip')
    os.remove('libtorch.zip')
else:
    print('Found libtorch')

hello_project = project('hello')
hello_project.compiler(cpp='g++', c='gcc')
hello_project.rpath = 'libtorch/lib'
hello_project.requires('nlohmann_json', version='3.11.2')
hello_project.depends('libtorch')
hello_project.find('Torch')

hello = cpp.executable(f'{hello_project.name}.out')
hello.options('-Wall -Werror')
hello.sources('hello.cpp')
hello.includes('.')
hello.defines('TEST')
hello.library_paths('/usr/lib')
# hello.after_build('./hello.out')
hello_project += hello

hello_project += cpp.shared_library('test', sources='test.cpp')

hello_project += cpp.static_library('testa', sources='test.cpp')

# hello_project += custom_target(
#     target_name='copy',
#     command='cp hello hello.out',
#     directory='.'
# )

# hello_project.add_subdirectory('sub')
