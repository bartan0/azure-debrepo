from sys import argv

from .lib import (
	az_upload,
	gpg_init,
	pkg_entry,
	gpg_pubkey,
	packages_append,
	in_release,
	pkg_upload,
	packages_upload,
	in_release_upload
)
from .secret import (
	USER_ID,
	STORAGE_ACCOUNT,
	CONTAINER,
	SAS_TOKEN
)

az_context = {
	'storage_account': STORAGE_ACCOUNT,
	'sas_token': SAS_TOKEN
}


def init ():
	fname = 'pubkey.gpg'

	gpg_init(USER_ID)
	gpg_pubkey(USER_ID, fname)

	az_upload(fname, CONTAINER, fname, **az_context)

def add (filename):
	entry = pkg_entry(filename)
	packages_append('buster', 'main', 'amd64', entry)
	in_release('buster', [ 'main' ], [ 'all', 'amd64' ])

	pkg_upload(filename, CONTAINER, entry, **az_context)
	packages_upload('buster', 'main', 'amd64', CONTAINER, **az_context)
	in_release_upload('buster', CONTAINER, **az_context)


if __name__ == '__main__':
	cmd = argv[1]

	dict(( f.__name__, f ) for f in [
		init,
		add
	])[cmd](*argv[2:])
