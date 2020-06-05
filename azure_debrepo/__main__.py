from functools import wraps
from io import StringIO
from os import (
	chdir,
	environ as env,
	path
)
from sys import argv, exit

from . import (
	__version__,
	AzureStorage,
	GPG,
	Packages,
	PackagesEntry,
	Release
)
from .cli import (
	cli,
	command,
	error,
	resolve
)


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
	entry = True
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

	return cli(cmd)(*args, **kwarg)


if __name__ == '__main__':
	exit(cli())
