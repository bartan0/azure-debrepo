import subprocess

from os import makedirs, path

from .lib import file_hash_size


class PackagesEntry:

	DEB_FIELDS = [
		'Package',
		'Version',
		'Architecture'
	]

	@classmethod
	def extract (cls, filename):
		h, s = file_hash_size(filename)
		proc = subprocess.run([ 'dpkg-deb', '--field', filename, *cls.DEB_FIELDS ],
			capture_output = True,
			universal_newlines = True
		)

		res = cls()
		res.filename = 'pool/%s.deb' % h
		res._fields = dict(( field.strip(), value.strip() ) for ( field, value ) in
			( line.split(':', 1) for line in proc.stdout.split('\n') if line )
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

	def get_path (self):
		return self._filename

	def append (self, entry):
		with open(self._filename, 'a') as f:
			entry.write(f)
