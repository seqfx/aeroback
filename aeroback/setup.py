try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Aeroback stores files from local disk to one or more storages supported by gsutil (AmazonS3, GoogleStorage)',
    'author': 'Orestes Cyllene',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'orestes.cyllene@gmail.com',
    'version': '0.3',
    'install_requires': ['nose'],
    'packages': ['aeroback'],
    'scripts': [],
    'name': 'aeroback'
}

setup(**config)
