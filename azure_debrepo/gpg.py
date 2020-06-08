from gpgme import (
	PROTOCOL_OpenPGP,
	SIG_MODE_CLEAR,
	Context
)
from os import chmod, makedirs, path


class GPG:

	def __init__ (self,
		homedir,
		keyfpr = None
	):
		gpgbin = path.join(homedir, 'gpg')
		ctx = self._context = Context()
		self._fpr = keyfpr
		self._key = None

		self.passphrase = None

		if not path.exists(homedir):
			makedirs(homedir, 0o700)

			open(path.join(homedir, 'gpg-agent.conf'), 'w').writelines(
				l + '\n' for l in [
					'default-cache-ttl 0'
				]
			)

			open(gpgbin, 'w').writelines(l + '\n' for l in [
				'#!/bin/bash',
				'exec gpg --pinentry-mode loopback "$@"'
			])

			chmod(gpgbin, 0o700)

		ctx.set_engine_info(PROTOCOL_OpenPGP, gpgbin, homedir)
		ctx.passphrase_cb = self._passphrase_cb

	def _get_key (self):
		if self._key is None:
			self._key = self._context.get_key(self._fpr)

		return self._key

	def _passphrase_cb (self, *args):
		open(args[3], 'w').write((self.passphrase or '') + '\n')

		return 0

	def genkey (self, passphrase, *,
		name = '',
		comment = '',
		email = ''
	):
		keyinfo = self._context.genkey('\n'.join([
			'<GnupgKeyParms format="internal">',
				'Key-Type: RSA',
				'Key-Length: 4096',
				'Passphrase: ' + passphrase,
				'Name-Real: ' + name if name else '',
				'Name-Comment: ' + comment if comment else '',
				'Name-Email: ' + email if email else '',
				'Expire-Date: 730',
			'</GnupgKeyParms>'
		]))

		self._fpr = keyinfo.fpr

	def clearsign (self, istream, ostream):
		self._context.signers = [ self._get_key() ]
		self._context.sign(istream, ostream, SIG_MODE_CLEAR)

	def pubkey (self,
		ostream,
		armor = False
	):
		self._context.armor = armor
		self._context.export(self._fpr, ostream)
