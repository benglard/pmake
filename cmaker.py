import os
import sys
import argparse
from pathlib import Path
from textwrap import dedent
import requests
import zipfile

import cpp

def _execute_makescript(path):
    path = Path(path)
    if path.is_dir():
        path = path / 'make.py'
    elif path.is_file():
        pass
    else:
        raise FileNotFoundError(path)

    contents = path.read_text()
    ARGS = _parse_args()
    exec(contents, globals(), locals())
    for key, value in locals().items():
        if isinstance(value, project):
            return value

def _parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str)
    parser.add_argument('--write', '-w', action='store_true')
    parser.add_argument('--configure', '-c', action='store_true')
    parser.add_argument('--build', '-b', action='store_true')
    parser.add_argument('--install', '-i', action='store_true')
    parser.add_argument('--mode', type=str, default='debug')
    parser.add_argument('--build-folder', '-bf', type=str, default='build')
    parser.add_argument('--install-folder', '-if', type=str, default='install')
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--jobs', '-j', type=int, default=1)
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_known_args(args)[0]
    return args

class project:

    def __init__(self, name, version='3.10'):
        self.name = name
        self._version = version
        self.rpath = ''
        self._vars = {}
        self._conans = {}
        self._pkgs = {}
        self._prefixes = []
        self._args = _parse_args()
        self._targets = []

    def version(self, version):
        self._version = version

    def __setitem__(self, key, value):
        self._vars[key] = value
    def __getitem__(self, key):
        return self._vars[key]
    def __contains__(self, key):
        return key in self._vars
    
    def requires(self, pkg, version=''):
        self._conans[pkg] = {'version': version}

    def depends(self, depends):
        self._prefixes.append(depends)

    def find(self, pkg, version='', required=True):
        self._pkgs[pkg] = {
            'version': version,
            'required': required
        }

    def compiler(self, c='', cpp=''):
        if c:
            self._vars['CMAKE_C_COMPILER'] = c
        if cpp:
            self._vars['CMAKE_CXX_COMPILER'] = cpp

    def _write(self):
        cmake = f'cmake_minimum_required(VERSION {self._version})\nproject({self.name})\n'
        if self.rpath:
            cmake += f'set(CMAKE_INSTALL_RPATH "{self.rpath}")\n'
        for key, value in self._vars.items():
            cmake += f'set({key} "{value}")\n'

        cmake += dedent("""
        if(NOT EXISTS "${CMAKE_BINARY_DIR}/conan.cmake")
            message(STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan")
            file(DOWNLOAD "https://raw.githubusercontent.com/opendocument-app/OpenDocument.core/main/cmake/conan.cmake"
                            "${CMAKE_BINARY_DIR}/conan.cmake"
                            TLS_VERIFY ON)
        endif()
        include(${CMAKE_BINARY_DIR}/conan.cmake)
        """)

        for pkg, data in self._conans.items():
            version = data['version']
            pkg = f'{pkg}/{version}'
            cmake += f'conan_cmake_run(REQUIRES {pkg} BASIC_SETUP CMAKE_TARGETS BUILD missing)\n'

        for prefix in self._prefixes:
            cmake += f'list(APPEND CMAKE_PREFIX_PATH {prefix})\n'

        for pkg, data in self._pkgs.items():
            version = data['version']
            required = 'REQUIRED' if data['required'] else ''
            cmake += f'find_package({pkg} {version} {required})\n'

        for target in self._targets:
            cmake += target.cmake()

        if self._args.verbose:
            print(cmake)

        with open('CMakeLists.txt', 'w') as f:
            f.write(cmake)

    def _configure(self):
        build_folder = Path(self._args.build_folder)
        build_folder.mkdir(parents=True, exist_ok=True)
        configure_cmd = f'cmake -S {self._args.path} -B {build_folder} -DCMAKE_INSTALL_PREFIX={self._args.install_folder} -DCMAKE_BUILD_TYPE={self._args.mode}'
        if self._args.verbose:
            configure_cmd += ' --verbose'
            print(configure_cmd)
        os.system(configure_cmd)

    def _build(self):
        build_cmd = f'cmake --build {self._args.build_folder} --config {self._args.mode} -j {self._args.jobs}'
        if self._args.verbose:
            build_cmd += ' --verbose'
        if self._args.clean:
            build_cmd += ' --clean-first'
        if self._args.verbose:
            print(build_cmd)
        os.system(build_cmd)

    def _install(self):
        install_cmd = f'cmake --install {self._args.build_folder} --config {self._args.mode}'
        if self._args.verbose:
            install_cmd += ' --verbose'
            print(install_cmd)
        os.system(install_cmd)

    def __iadd__(self, target):
        self._targets.append(target)
        return self
    
def download(url, filename):
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def unzip(filename, folder='.'):
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(folder)

if __name__ == '__main__':
    p = _execute_makescript(sys.argv[1])
    if p:
        if p._args.write:
            p._write()
        if p._args.configure:
            p._configure()
        if p._args.build:
            p._build()
        if p._args.install:
            p._install()