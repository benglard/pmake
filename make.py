hello_project = project('hello')

hello = cpp.executable('{}.out'.format(hello_project.name))
hello.set_compiler('g++')
hello.set_standard(14)
if project.mode == 'release':
    hello.set_optimization_level(3)
hello.add_debug_symbols()
hello.add_options('-Wall -Werror')
hello.add_source('hello.cpp')
hello.add_include('.')
hello.add_define('TEST')
hello.link_directory('/usr/lib')
hello.after_build('./hello.out')
hello.install('/Users/benglard/Desktop')
hello_project += hello

hello_project += cpp.shared_library('test', sources='test.cpp')

hello_project += cpp.static_library('testa', sources='test.cpp')

hello_project += custom_target(
    target_name='copy',
    command='cp hello hello.out',
    directory='.'
)

hello_project.add_subdirectory('sub')
