import os
import subprocess


class AzureStorage:

	def __init__ (self, container, *,
		account_name,
		sas_token
	):
		self._container = container
		self._account = account_name
		self._sas_token = sas_token

	def upload (self, filename, blobname):
		subprocess.run([ 'az', 'storage', 'blob', 'upload',
			'--container', self._container,
			'--file', filename,
			'--name', blobname
		],
			capture_output = True,
			env = {
				**os.environ,
				'AZURE_STORAGE_ACCOUNT': self._account,
				'AZURE_STORAGE_SAS_TOKEN': self._sas_token
			}
		)
