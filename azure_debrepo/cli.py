from functools import wraps
from getopt import GetoptError, getopt
from os import getcwd, path
from sys import argv, exit, stdout, stderr

_initwd = getcwd()
_commands = {}
_entry = None


def error (msg, status = 0):
	print('Error: %s' % msg, file = stderr)

	if status:
		exit(status)

def cli (command = None):
	if command is None:
		return _entry(*argv[1:])

	if command not in _commands:
		error('%s: Unknown command' % command, 2)

	return _commands[command]

def command (*,
	options = '',
	longopts = [],
	help = None,
	entry = False
):
	def decorator (f):
		@wraps(f)
		def g (*argv, **kwarg):
			try:
				opts, args = getopt(argv,
					options if help is None else options + 'h',
					longopts if help is None else longopts + [ 'help' ]
				)

			except GetoptError as err:
				error(err, 2)

			opts = dict(((opt[2:] if opt.startswith('--') else opt[1:]).replace('-', '_'), val) for opt, val in opts)

			if help is not None and ('h' in opts or 'help' in opts):
				stdout.write(help)

				return 0

			return f(*args, **opts, **kwarg)

		global _entry

		if entry:
			_entry = g
		else:
			_commands[f.__name__] = g

		return g

	return decorator

def resolve (p):
	if path.isabs(p):
		return p

	return path.join(_initwd, p)
