from os import path, makedirs
from glob import glob
from email.utils import formatdate

from .lib import file_hash_size


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

	def get_dirpath (self):
		return self._root

	def write (self, stream):
		stream.write('\n'.join('%s: %s' % pair for pair in self._fields.items()))
		stream.write(
			'\nSHA256:\n' +
			'\n'.join([ '\t%s %d %s' % (*file_hash_size(p), path.relpath(p, self._root))
				for p in glob('%s/**/Packages' % self._root, recursive = True)
			]) +
			'\n'
		)

		return stream
