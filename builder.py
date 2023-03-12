from sys import argv
from collections import namedtuple
from glob import glob
from platform import system as platform_system
from os.path import join as path_join
import os.path

import cpp_old

__BUILD_MODE__ = ''

if len(argv) > 2:
    mode_str = '--mode='
    for elem in argv[2:]:
        if mode_str in elem:
            _, __BUILD_MODE__ = elem.split(mode_str)

custom_target = namedtuple('custom_target', 'target_name command directory')

def _execute_makescript(path):
    if os.path.isdir(path):
        path = path_join(path, 'make.py')
    elif os.path.isfile(path):
        pass

    with open(path) as fi:
        contents = fi.read()
        exec(contents, globals(), locals())
        for key, value in locals().items():
            if isinstance(value, project):
                return value

class project(object):
    mode = __BUILD_MODE__

    def __init__(self, name, directory='.'):
        self.name = name
        self._directory = directory
        self._makefile = open(path_join(directory, 'Makefile'), 'w')
        self.targets = []
        self.custom_targets = []
        self.other_projects = []

    def __del__(self):
        system = platform_system()
        target_names = []
        target_outputs = []
        num_targets = float(sum(t.num_targets for t in self.targets))
        self._makefile.write('all: all_targets\n')

        target_index = 0
        for target in self.targets:
            subobjects, cmd, depends, output = target.build(system)
            for subtarget in subobjects:
                _, subcmd, subdepends, suboutput = subtarget.build(system)
                target_name = subtarget.target_name
                if suboutput in target_outputs:
                    # dont rebuild targets already built
                    continue

                target_outputs.append(suboutput)
                percent_done = int(round((target_index + 1) / num_targets * 100))
                self._makefile.write('{}: {}\n\t@{}\n\t@echo \'\033[1m\033[32m[{}%] Building {} => {}\033[0m\'\n\t@{}\n\t@{}\n'.format(
                    target_name,
                    subdepends,
                    subtarget.before_build_cmd,
                    percent_done,
                    subdepends,
                    target_name,
                    subcmd,
                    subtarget.after_build_cmd
                ))
                target_index += 1

            target_name = target.target_name
            target_names.append(target_name)
            target_outputs.append(output)
            percent_done = int(round((target_index + 1) / num_targets * 100))
            if target.install_path is not None:
                install_cmd = 'cp {} {}'.format(
                    output, target.install_path)
            else:
                install_cmd = ''

            self._makefile.write('{}: {}\n\t{}\n\t@echo \'\033[1m\033[32m[{}%] Building {}\033[0m\'\n\t@{}\n\t{}\n\t{}\n'.format(
                target_name,
                depends,
                target.before_build_cmd,
                percent_done,
                target_name,
                cmd,
                target.after_build_cmd,
                install_cmd
            ))
            target_index += 1

        for target in self.custom_targets:
            self._makefile.write('{}:\n\tcd {} && {}\n'.format(
                target.target_name, target.directory, target.command))

        for proj_name, directory in self.other_projects:
            self._makefile.write('{}:\n\t@cd {} && make all\n'.format(proj_name, directory))
            self._makefile.write('.PHONY: {}\n'.format(proj_name))
            target_names.append(proj_name)

        self._makefile.write(
            'all_targets: {}\n\t@echo \'\033[1m\033[32m[100%] Done\033[0m\'\n'
            .format(' '.join(target_names)))

        clean_str = 'clean:\n\t@rm {}\n'.format(' '.join(target_outputs))
        for proj_name, directory in self.other_projects:
            clean_str += '\t@cd {} && make clean\n'.format(directory)
        self._makefile.write(clean_str)

        self._makefile.close()

    def add(self, target):
        if isinstance(target, custom_target):
            self.custom_targets.append(target)
        elif isinstance(target, project):
            self.other_projects.append(target)
        else:
            self.targets.append(target)

    def __iadd__(self, t):
        self.add(t)
        return self

    def add_subdirectory(self, directory, filename='make.py'):
        next_script = path_join(directory, filename)
        rv_project = _execute_makescript(next_script)
        next_project = project(rv_project.name, directory=directory)
        next_project.targets = rv_project.targets
        next_project.custom_targets = rv_project.custom_targets
        self.other_projects.append((next_project.name, directory))

if __name__ == '__main__':
    _execute_makescript(argv[1])
