from functools import wraps
from getopt import GetoptError, getopt
from io import StringIO
from os import (
	chdir,
	environ as env,
	getcwd,
	path
)
from sys import argv, exit, stdout, stderr

from . import (
	__version__,
	AzureStorage,
	GPG,
	Packages,
	PackagesEntry,
	Release
)

initwd = getcwd()
commands = {}


def error (msg, status = 0):
	print('Error: %s' % msg, file = stderr)

	if status:
		exit(status)

def resolve (p):
	if path.isabs(p):
		return p

	return path.join(initwd, p)

def command (*,
	options = '',
	longopts = [],
	help = None,
	internal = False
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

		if not internal:
			commands[f.__name__] = g

		return g

	return decorator


def with_gpg (f):
	@wraps(f)
	def g (*args,
		gpg_home = None,
		gpg_user = None,
		**kwarg
	):
		return f(*args, **kwarg,
			gpg = GPG(
				gpg_home or env.get('GNUPGHOME') or 'gpg',
				gpg_user or env['USER']
			)
		)

	return g

def with_storage (f):
	@wraps(f)
	def g (*args,
		azure_container = None,
		azure_account = None,
		azure_token = None,
		**kwarg
	):
		return f(*args, **kwarg,
			storage = AzureStorage(azure_container or env['AZURE_STORAGE_CONTAINER'],
				account_name = azure_account or env['AZURE_STORAGE_ACCOUNT'],
				sas_token = azure_token or env['AZURE_STORAGE_SAS_TOKEN'],
			)
		)

	return g


@command(
	longopts = [
		'pubkey=',
		'azure-pubkey='
	]
)
@with_gpg
@with_storage
def init (*args,
	gpg,
	storage,
	pubkey = 'pubkey.gpg',
	azure_pubkey = None
):
	fname = 'pubkey.gpg'
	gpg.genkey()

	with open(pubkey, 'wb') as f:
		gpg.pubkey(f)

	storage.upload(
		pubkey,
		azure_pubkey or pubkey
	)


@command(
	longopts = [
		'suite=',
		'component=',
		'arch='
	]
)
@with_gpg
@with_storage
def add (*args,
	gpg,
	storage,
	suite = None,
	component = 'main',
	arch = 'amd64'
):
	if suite is None:
		error('Suite must be specified', 2)

	try:
		filename = resolve(args[0])
	except IndexError:
		error('DEB package file name required', 2)

	entry = PackagesEntry.extract(filename)
	packages = Packages('.',
		suite = suite,
		component = component,
		arch = arch
	)
	release = Release('.',
		suite = suite,
		components = [ component ],
		archs = [ arch ]
	)

	packages.append(entry)
	s = release.write(StringIO())

	p_packages = packages.get_path()
	p_inrelease = release.get_dirpath() + '/InRelease'

	with open(p_inrelease, 'wb') as f:
		gpg.clearsign(s.getvalue().encode('utf8'), f)

	storage.upload(p_packages, path.relpath(p_packages, '.'))
	storage.upload(p_inrelease, path.relpath(p_inrelease, '.'))
	storage.upload(filename, entry.filename)


@command(
	help =
'''%s - manage Debian repository in Azure blob storage

Options:

	-h, --help    Show this help message

''' % (
	argv[0]
),
	options = 'V',
	longopts = [
		'azure-container=',
		'azure-account=',
		'azure-token=',
		'gpg-home=',
		'gpg-user=',
		'workdir=',
		'version'
	],
	internal = True
)
def _main (*args,
	V = None,
	workdir = None,
	version = None,
	**kwarg
):
	if V is not None or version is not None:
		print('v%s' % __version__)

		return 0

	cmd, *args = args

	if workdir is not None:
		if not path.exists(workdir):
			error('%s: Requested workdir does not exist' % workdir, 1)

		chdir(workdir)

	if cmd not in commands:
		error('%s: Unknown command' % cmd, 2)

	return commands[cmd](*args, **kwarg)


if __name__ == '__main__':
	exit(_main(*argv[1:]))
