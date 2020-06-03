from sys import argv
from io import StringIO
from os import path
from functools import wraps

from . import (
	AzureStorage,
	GPG,
	Packages,
	PackagesEntry,
	Release
)
from .secret import (
	USER_ID,
	STORAGE_ACCOUNT,
	CONTAINER,
	SAS_TOKEN
)


def with_gpg (f):
	@wraps(f)
	def wrapper (*args):
		f(GPG('gpg', USER_ID), *args)

	return wrapper


def with_storage (f):
	@wraps(f)
	def wrapper (*args):
		f(AzureStorage(CONTAINER,
			account_name = STORAGE_ACCOUNT,
			sas_token = SAS_TOKEN
		), *args)

	return wrapper


@with_gpg
@with_storage
def init (storage, gpg):
	fname = 'pubkey.gpg'
	gpg.genkey()

	with open(fname, 'wb') as f:
		gpg.pubkey(f)

	storage.upload(fname, fname)

@with_gpg
@with_storage
def add (storage, gpg, filename):
	entry = PackagesEntry.extract(filename)
	packages = Packages('.',
		suite = 'buster',
		component = 'main',
		arch = 'amd64'
	)
	release = Release('.',
		suite = 'buster',
		components = [ 'main' ],
		archs = [ 'amd64' ]
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


if __name__ == '__main__':
	cmd = argv[1]

	dict(( f.__name__, f ) for f in [
		init,
		add
	])[cmd](*argv[2:])
