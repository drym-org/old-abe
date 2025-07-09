from setuptools import setup

requirements = []

test_requirements = [
    'pytest',
    'pytest-sugar',
    'pytest-tldr',
    'pyfakefs',
    'time_machine',
    'tox',
    'tox-gh-actions',
    'coveralls',
]

dev_requirements = ['flake8', 'black']

setup_requirements = ['pytest-runner']

setup(
    name='oldabe',
    version='0.0.0',
    description='Accountant for all of your ABE needs.',
    author='Old Abe',
    author_email='abe@drym.org',
    url='https://github.com/drym-org/old-abe',
    include_package_data=True,
    packages=['oldabe'],
    test_suite='tests',
    install_requires=requirements,
    setup_requires=setup_requirements,
    extras_require={'dev': dev_requirements, 'test': test_requirements},
)
