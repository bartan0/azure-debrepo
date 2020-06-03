import subprocess

from os import makedirs, path


# TODO: should be in lib
#
from hashlib import sha256
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


class PackagesEntry:

	@classmethod
	def extract (cls, filename):
		h, s = file_hash_size(filename)
		data = subprocess.run([ 'sh', '-c', 'dpkg --ctrl-tarfile %s | tar -xO' % filename ],
			capture_output = True,
			universal_newlines = True
		)

		res = cls()
		res.filename = 'pool/%s.deb' % h
		res._fields = dict(( field.strip(), value.strip() ) for ( field, value ) in
			( line.split(':', 1) for line in data.stdout.split('\n') if line )
		)
		res._fields.update(
			Filename = res.filename,
			Size = s,
			SHA256 = h
		)

		return res

	def write (self, stream):
		stream.writelines('%s: %s\n' % item for item in self._fields.items())
		stream.write('\n')


class Packages:

	def __init__ (self, repo_root, *,
		suite,
		component,
		arch
	):
		dirpath = '%s/dists/%s/%s/binary-%s' % (
			path.abspath(repo_root),
			suite,
			component,
			arch
		)
		makedirs(dirpath, exist_ok = True)

		self._filename = dirpath + '/Packages'

	def append (self, entry):
		with open(self._filename, 'a') as f:
			entry.write(f)
