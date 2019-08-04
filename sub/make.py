subproject = project('sub')
subproject += cpp.executable(('{}.out'.format(subproject.name)), sources='sub.cpp')
