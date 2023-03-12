_DEFAULT_CPP_COMPILER = 'c++'
_DEFAULT_ARCHIVER = 'ar'

def _wrap_list(arg, array_name):
    if isinstance(arg, list):
        return arg
    if isinstance(arg, tuple):
        return list(arg)
    if isinstance(arg, str):
        return [arg]
    else:
        error_str = 'invalid type {} for {}'.format(type(arg), array_name)
        raise TypeError(error_str)

class _Target(object):
    def __init__(
        self,
        target_name,
        sources = [],
        includes = [],
        libraries = [],
        options = [],
        defines = {}
    ):
        self.target_name = target_name
        self.before_build_cmd = ''
        self.after_build_cmd = ''
        self._cxx_compiler = _DEFAULT_CPP_COMPILER
        self._archiver = _DEFAULT_ARCHIVER
        self._subobjects = []

        self._sources = []
        self._includes = []
        self._libraries = []
        self._options = []
        self._defines = {}
        self._library_paths = []
        self.install_path = None

        self.add_sources(sources)
        self.add_includes(includes)
        self.add_libraries(libraries)
        self.add_options(options)
        self.add_defines(defines)

    def add_sources(self, arg):
        self._sources.extend(_wrap_list(arg, 'sources'))
    add_source = add_sources

    def add_includes(self, arg):
        self._includes.extend(_wrap_list(arg, 'includes'))
    add_include = add_includes

    def add_libraries(self, arg):
        self._libraries.extend(_wrap_list(arg, 'libraries'))
    add_library = add_libraries

    def add_options(self, arg):
        self._options.extend(_wrap_list(arg, 'options'))
    add_option = add_options

    def add_defines(self, arg, value=None):
        if isinstance(arg, dict):
            self._defines.update(arg)
        elif isinstance(arg, str):
            self._defines[arg] = value
        else:
            error_str = 'invalid type {} for defines'.format(type(arg))
            raise TypeError(error_str)
    add_define = add_defines

    def link_directories(self, arg):
        self._library_paths.extend(_wrap_list(arg, 'library paths'))
    link_directory = link_directories

    def set_archiver(self, archiver):
        self._archiver = archiver

    def set_compiler(self, compiler):
        self._cxx_compiler = compiler

    def set_standard(self, version):
        if version in (11, 14, 17, 20):
            self._options.append('-std=c++{}'.format(version))
        elif version == 3:
            self._options.append('-std=c++03')
        else:
            raise ValueError('Invalid cpp version {}'.format(version))

    def add_debug_symbols(self):
        self._options.append('-g')

    def set_optimization_level(self, level):
        if level < 0 or level > 3:
            raise ValueError('Optimization level must be between 0-3')
        self._options.append('-O{}'.format(level))

    def build(self):
        raise NotImplementedError('_Target.build not implemented')

    def before_build(self, command, directory='.'):
        self.before_build_cmd = 'cd {} && {}'.format(directory, command)

    def after_build(self, command, directory='.'):
        self.after_build_cmd = 'cd {} && {}'.format(directory, command)

    def _build_subobjects(self):
        self._subobjects = [
            object_file(
                '{}.o'.format(source),
                sources=source,
                includes=self._includes,
                libraries=self._libraries,
                options=self._options,
                defines=self._defines
            ) for source in self._sources
        ]

    def install(self, path):
        self.install_path = path

    @property
    def num_targets(self):
        return len(self._sources) + 1

class object_file(_Target):
    def build(self, system):
        include_str = ' '.join(['-I {}'.format(inc) for inc in self._includes])
        library_str = ' '.join(['-l{}'.format(lib) for lib in self._libraries])
        library_path_str = ' '.join(['-L {}'.format(inc) for inc in self._library_paths])
        sources_str = ' '.join(self._sources)

        define_str = ''
        for key, value in self._defines.items():
            if value is None:
                define_str += '-D{}'.format(key)
            else:
                define_str += '-D{}={}'.format(key, value)

        self._options.append('-c')

        if self.target_name.endswith('.o'):
            target_output = self.target_name
        else:
            ext = 'o'
            target_output = '{}.{}'.format(self.target_name, ext)

        cmd = '{} {} {} {} {} {} -o {} {}'.format(
            self._cxx_compiler,
            ' '.join(self._options),
            define_str,
            include_str,
            library_path_str,
            sources_str,
            target_output,
            library_str
        )

        return self._subobjects, cmd, sources_str, target_output

class executable(_Target):
    def build(self, system):
        self._build_subobjects()

        include_str = ' '.join(['-I {}'.format(inc) for inc in self._includes])
        library_str = ' '.join(['-l{}'.format(lib) for lib in self._libraries])
        library_path_str = ' '.join(['-L {}'.format(inc) for inc in self._library_paths])
        sources_str = ' '.join([ obj.target_name for obj in self._subobjects ])

        define_str = ''
        for key, value in self._defines.items():
            if value is None:
                define_str += '-D{}'.format(key)
            else:
                define_str += '-D{}={}'.format(key, value)

        if system == 'Windows':
            ext = '.exe'
        else:
            ext = ''
        target_output = '{}'.format(self.target_name, ext)

        cmd = '{} {} {} {} {} -o {} {} {}'.format(
            self._cxx_compiler,
            ' '.join(self._options),
            define_str,
            include_str,
            library_path_str,
            target_output,
            sources_str,
            library_str
        )

        return self._subobjects, cmd, sources_str, target_output

class shared_library(_Target):
    def build(self, system):
        self._build_subobjects()

        include_str = ' '.join(['-I {}'.format(inc) for inc in self._includes])
        library_str = ' '.join(['-l{}'.format(lib) for lib in self._libraries])
        library_path_str = ' '.join(['-L {}'.format(inc) for inc in self._library_paths])
        sources_str = ' '.join([ obj.target_name for obj in self._subobjects ])

        define_str = ''
        for key, value in self._defines.items():
            if value is None:
                define_str += '-D{}'.format(key)
            else:
                define_str += '-D{}={}'.format(key, value)

        self._options.append('-fPIC -shared')

        if system == 'Windows':
            ext = 'dll'
        elif system == 'Darwin':
            ext = 'dylib'
        else:
            ext = 'so'
        target_output = '{}.{}'.format(self.target_name, ext)

        cmd = '{} {} {} {} {} -o {} {} {}'.format(
            self._cxx_compiler,
            ' '.join(self._options),
            define_str,
            include_str,
            library_path_str,
            target_output,
            sources_str,
            library_str
        )

        return self._subobjects, cmd, sources_str, target_output

class static_library(_Target):
    def build(self, system):
        self._build_subobjects()

        sources_str = ' '.join([ obj.target_name for obj in self._subobjects ])

        if system == 'Windows':
            ext = 'lib'
        else:
            ext = 'a'
        target_output = '{}.{}'.format(self.target_name, ext)

        cmd = '{} rcs {} {}'.format(
            self._archiver,
            target_output,
            sources_str,
        )

        return self._subobjects, cmd, sources_str, target_output
