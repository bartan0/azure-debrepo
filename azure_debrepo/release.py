from os import path, makedirs
from glob import glob
from hashlib import sha256
from email.utils import formatdate


# TODO: should be in lib
#
def file_hash_size (filename):
	buffer = bytearray(4096)
	hash = sha256()
	size = 0

	with open(filename, 'rb') as f:
		n_read = f.readinto(buffer)

		hash.update(buffer if n_read == len(buffer) else buffer[:n_read])
		size += n_read

	return hash.digest().hex(), size



class Release:

	def __init__ (self, repo_root, *,
		suite,
		components,
		archs
	):
		self._root = '%s/dists/%s' % (path.abspath(repo_root), suite)
		makedirs(self._root, exist_ok = True)

		self._fields = dict(
			Codename = suite,
			Components = ' '.join(components),
			Architectures = ' '.join(archs),
			Date = formatdate(),
		)

	def write (self, stream):
		stream.write('\n'.join('%s: %s' % pair for pair in self._fields.items()))
		stream.write(
			'\nSHA256:\n' +
			'\n'.join([ '\t%s %d %s' % (*file_hash_size(p), path.relpath(p, self._root))
				for p in glob('%s/**/Packages' % self._root, recursive = True)
			]) +
			'\n'
		)
