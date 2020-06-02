import subprocess

from os import path, makedirs, environ


class GPG:

	def __init__ (self, homedir, user_id):
		self._user_id = user_id
		self._homedir = path.abspath(homedir)
		makedirs(self._homedir, 0o700, True)

	def _gpg (self, *args, **kwarg):
		return subprocess.run([ 'gpg', *args ],
			env = {
				**environ,
				'GNUPGHOME': self._homedir
			},
			**kwarg
		)

	def genkey (self):
		self._gpg('--quick-gen-key', '--batch', '--passphrase', '', self._user_id,
			capture_output = True
		)

	def pubkey (self, stream):
		self._gpg('--export', self._user_id,
			stdout = stream
		)

	def clearsign (self, data, stream):
		self._gpg('--clearsign',
			input = data,
			stdout = stream
		)
