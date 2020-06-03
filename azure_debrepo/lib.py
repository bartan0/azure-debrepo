import sys

from os import path, makedirs, environ
from subprocess import run
from hashlib import sha256
from email.utils import formatdate


def in_release (dist, *args):
	gpg([ '--clearsign' ],
		input = bytes('\n'.join('%s: %s' % x for x in release(dist, *args).items()), 'utf8'),
		stdout = open('dists/%s/InRelease' % dist, 'wb')
	)




def packages_upload (dist, component, arch, container,
	**kwarg
):
	fname = 'dists/%s/%s/binary-%s/Packages' % (dist, component, arch)

	return az_upload(fname, container, fname,
		**kwarg
	)

def in_release_upload (dist, container,
	**kwarg
):
	fname = 'dists/%s/InRelease' % dist

	return az_upload(fname, container, fname,
		**kwarg
	)
