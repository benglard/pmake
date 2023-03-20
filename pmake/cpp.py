from pathlib import Path
from inspect import isgenerator

def _wrap_list(arg):
    if arg is None:
        return []
    if isinstance(arg, list):
        return arg
    if isinstance(arg, tuple):
        return list(arg)
    if isinstance(arg, Path):
        return [str(arg)]
    if isgenerator(arg):
        return list(map(str, arg))
    return [arg]

class _Target:

    def __init__(
        self,
        target_type,
        name='',
        sources=None,
        includes=None,
        libraries=None,
        options=None,
        library_paths=None,
        defines=None,
        properties=None,
    ):
        self.type = target_type
        self.name = name
        self._sources = _wrap_list(sources)
        self._includes = _wrap_list(includes)
        self._libraries = _wrap_list(libraries)
        self._options = _wrap_list(options)
        self._library_paths = _wrap_list(library_paths)
        self._defines = _wrap_list(defines)
        self._properties = properties or {}

    def cmake(self):
        assert self.name and self.type and self._sources
        if self.type == 'shared_library':
            rv = f'add_library({self.name} SHARED)'
        elif self.type == 'static_library':
            rv = f'add_library({self.name} STATIC)'
        elif self.type == 'executable':
            rv = f'add_executable({self.name})'
        else:
            raise Exception(f'Unknown target type: {self.type}')
        rv += self._cmake_cmd_list('target_sources', self._sources)
        rv += self._cmake_cmd_list('target_include_directories', self._includes)
        rv += f'\ntarget_include_directories({self.name} PUBLIC ${{CONAN_INCLUDE_DIRS}})'
        rv += self._cmake_cmd_list('target_link_libraries', self._libraries)
        rv += f'\ntarget_link_libraries({self.name} ${{CONAN_LIB_DIRS}})'
        rv += self._cmake_cmd_list('target_compile_options', self._options)
        rv += self._cmake_cmd_list('target_link_directories', self._library_paths)
        rv += self._cmake_cmd_list('target_compile_definitions', self._defines)
        rv += self._cmake_cmd_dict('set_target_properties', self._properties, 'PROPERTIES')
        rv += '\n'
        return rv
    
    def sources(self, *sources):
        self._sources.extend(sources)
    def includes(self, *includes):
        self._includes.extend(includes)
    def libraries(self, *libraries):
        self._libraries.extend(libraries)
    def options(self, *options):
        self._options.extend(options)
    def library_paths(self, *library_paths):
        self._library_paths.extend(library_paths)
    def defines(self, *defines):
        self._defines.extend(defines)
    def properties(self, **properties):
        self._properties.update(properties)

    def _cmake_cmd_list(self, cmd, lst, public=True):
        if len(lst) == 0:
            return ''
        public_str = 'PUBLIC' if public else 'PRIVATE'
        lst_str = ' '.join(lst)
        rv = f'\n{cmd}({self.name} {public_str} {lst_str})'
        return rv
    
    def _cmake_cmd_dict(self, cmd, dct, keyword=''):
        if len(dct) == 0:
            return ''
        rv = ''
        for key, value in dct.items():
            key = key.upper()
            value = str(value)

            rv += f'\n{cmd}({self.name} {keyword} {key} {value})'
        return rv

def shared_library(*args, **kwargs):
    return _Target('shared_library', *args, **kwargs)
def static_library(*args, **kwargs):
    return _Target('static_library', *args, **kwargs)
def executable(*args, **kwargs):
    return _Target('executable', *args, **kwargs)