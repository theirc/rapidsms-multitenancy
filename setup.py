import os
from setuptools import setup, find_packages


required_packages = [
    'django>=1.3',
]


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


setup(
    name='django-multitenancy',
    version=__import__('multitenancy').__version__,
    author='International Rescue Committee',
    author_email='rescuesms-team@caktusgroup.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/theirc/rapidsms_multitenancy',
    license='BSD',
    description=' '.join(__import__('multitenancy').__doc__.splitlines()).strip(),
    classifiers=[
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Framework :: Django',
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
    ],
    long_description=read_file('README.rst'),
    tests_require=required_packages,
    test_suite="runtests.runtests",
    install_requires=required_packages,
    zip_safe=False,
)
