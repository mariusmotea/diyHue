from setuptools import setup


setup(name='huebridgeemulator',
      version='0.0.1',
      description='',
      author='',
      author_email='',
      url='https://github.com/mariusmotea/diyHue',
      package_data={'': ['LICENSE.txt', 'requirements.txt', 'test_requirements.txt']},
      include_package_data=True,
      packages=['huebridgeemulator'],
      entry_points={
          'console_scripts': [
              'huebridgeemulator = huebridgeemulator.__main__:main'
          ]
      },
      license='Apache 2.0',
      install_requires=["requests==2.19.1",
                        "PyYAML==3.12",
                        "hug==2.4.0",
                        "Jinja2==2.10",
                        "astral==1.6.1",
                        ],
      classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ],
)
