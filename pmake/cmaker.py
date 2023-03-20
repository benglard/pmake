import os
import argparse
from pathlib import Path
from textwrap import dedent
import requests
import zipfile

def _make_folder(path, extra):
    if len(extra) == 0:
        return path
    bf = Path(extra)
    if bf.is_absolute() and not bf.exists():
        bf.mkdir(parents=True)
    elif not bf.is_absolute():
        bf = path.parent / bf
        if not bf.exists():
            bf.mkdir(parents=True)
    return bf

def _parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default='.')
    parser.add_argument('--write', '-w', action='store_true')
    parser.add_argument('--configure', '-c', action='store_true')
    parser.add_argument('--build', '-b', action='store_true')
    parser.add_argument('--install', '-i', action='store_true')
    parser.add_argument('--mode', type=str, default='debug')
    parser.add_argument('--build-folder', '-bf', type=str, default='build')
    parser.add_argument('--install-folder', '-if', type=str, default='')
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--jobs', '-j', type=int, default=1)
    parser.add_argument('--verbose', '-v', action='store_true')
    args, unknown = parser.parse_known_args(args)

    path = Path(args.path)
    if path.is_dir():
        path = path / 'make.py'
    elif path.is_file():
        pass
    else:
        raise FileNotFoundError(path)
    args.path = path
    args.source_folder = path.parent
    args.build_folder = _make_folder(path, args.build_folder)
    args.install_folder = _make_folder(path, args.install_folder)

    return args, unknown

class project:

    def __init__(self, name, version='3.10', extra_args_parser=None):
        self.name = name
        self._version = version
        self.rpath = ''
        self._vars = {}
        self._conans = {}
        self._pkgs = {}
        self._prefixes = []
        self._args, extra = _parse_args()
        if extra_args_parser:
            self._extra_args = extra_args_parser.parse_known_args(extra)[0]
        self._targets = []

    @property
    def args(self):
        return self._args
    
    @property
    def extra_args(self):
        return self._extra_args

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

    def write(self):
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

        path = self._args.source_folder / 'CMakeLists.txt'
        with open(path, 'w') as f:
            f.write(cmake)
        print(f'Wrote {path}')

    def configure(self):
        configure_cmd = f'cmake -S {self._args.source_folder} -B {self._args.build_folder} -DCMAKE_BUILD_TYPE={self._args.mode}'
        if self._args.install_folder:
            configure_cmd += f' -DCMAKE_INSTALL_PREFIX={self._args.install_folder}'
        if self._args.verbose:
            # configure_cmd += ' --verbose'
            print(configure_cmd)
        os.system(configure_cmd)

    def build(self):
        build_cmd = f'cmake --build {self._args.build_folder} --config {self._args.mode} -j {self._args.jobs}'
        if self._args.verbose:
            build_cmd += ' --verbose'
        if self._args.clean:
            build_cmd += ' --clean-first'
        if self._args.verbose:
            print(build_cmd)
        os.system(build_cmd)

    def install(self):
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

def unzip(filename, extract_path):
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

def fetch_contents(url, download_path, always_download=False, check_path=None, do_unzip=False, extract_path=None, remove_zip=True):
    if not check_path:
        check_path = download_path
    if always_download or not check_path.exists():
        print(f'Downloading {url} to {download_path}')
        download(url, download_path)
        
    if check_path.exists():
        print(f'Found {check_path}')
        return

    if do_unzip:
        print(f'Unzipping {download_path}')
        if not extract_path:
            extract_path = download_path
        unzip(download_path, extract_path)

        if remove_zip:
            print(f'Removing {download_path}')
            download_path.unlink()