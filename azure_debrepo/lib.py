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


from hashlib import sha256

def file_hash_size (filename):
	buffer = bytearray(4096)
	hash = sha256()
	size = 0

	with open(filename, 'rb') as f:
		n_read = f.readinto(buffer)

		hash.update(buffer if n_read == len(buffer) else buffer[:n_read])
		size += n_read

	return hash.digest().hex(), size
