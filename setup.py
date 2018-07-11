#!/usr/bin/env python3
import os

from setuptools import setup
from setuptools import setup, find_packages

def package_files(dest, directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join(path, filename))
    return (dest, paths)

DATA_FILES = []
DATA_FILES.append(package_files('templates', 'huebridgeemulator/web/templates'))
DATA_FILES.append(package_files('web-ui', 'huebridgeemulator/web/web-ui'))
print(DATA_FILES)

PACKAGES = find_packages(exclude=['tests', 'tests.*'])


setup(name='huebridgeemulator',
      version='0.0.1',
      description='',
      author='',
      author_email='',
      url='https://github.com/mariusmotea/diyHue',
      package_data={'': ['LICENSE.txt', 'requirements.txt', 'test_requirements.txt'],
                    },
      data_files=DATA_FILES,
      include_package_data=True,
      packages=PACKAGES,
      entry_points={
          'console_scripts': [
              'huebridgeemulator = huebridgeemulator.__main__:main'
          ]
      },
      license='Apache 2.0',
      zip_safe=False,
      platforms='any',
      install_requires=[
                        "requests==2.19.1",
                        "PyYAML==3.12",
                        "hug==2.4.0",
                        "Jinja2==2.10",
                        "astral==1.6.1",
                        "netifaces==0.10.7",
                        "tzlocal==1.5.1",
                        "yeelight==0.4.2",
                        "pyHS100==0.3.2",
                        ],
      classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ],
)
