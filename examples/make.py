from pmake import project
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

hello_project += cpp.shared_library('test', sources='test.cpp')

hello_project += cpp.static_library('testa', sources='test.cpp')

hello_project.write()
hello_project.configure()
hello_project.build()
hello_project.install()