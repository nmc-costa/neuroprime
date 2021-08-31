# -*- coding: utf-8 -*-

# Copyright (C) 2017-2020 Nuno da Costa <id6814@alunos.uminho.pt>

#simple (https://stackoverflow.com/questions/6323860/sibling-package-imports/50193944#50193944)
#from setuptools import setup, find_packages
#
#setup(name='neuroprime', version='1.0', packages=find_packages())

#complex (like mne)
import os
from os import path as op

from setuptools import setup

#getting version from __init__.py
version = None
with open(os.path.join('neuroprime', '__init__.py'), 'r') as fid:
    for line in (line.strip() for line in fid):
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('\'')
            break
if version is None:
    raise RuntimeError('Could not determine version')


descr = """neuroprime distribution with pylsl for BCI online applications, specifically closed loop Neurofeedback"""

DISTNAME = "neuroprime"
DESCRIPTION = descr
MAINTAINER = 'Nuno Costa'
MAINTAINER_EMAIL = ''
URL = ''
LICENSE = 'GPL-2.0 License'
DOWNLOAD_URL = ''
VERSION = version


def package_tree(pkgroot):
    """Get the submodule list."""
    # Adapted from MNE-Python
    path = os.path.dirname(__file__)
    subdirs = [os.path.relpath(i[0], path).replace(os.path.sep, '.')
               for i in os.walk(os.path.join(path, pkgroot))
               if '__init__.py' in i[2]]
    return sorted(subdirs)

if __name__ == "__main__":
    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    setup(name=DISTNAME,
          maintainer=MAINTAINER,
          include_package_data=True,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          license=LICENSE,
          url=URL,
          version=VERSION,
          download_url=DOWNLOAD_URL,
          long_description=open('README.md').read(),
          zip_safe=True,  # the package can run out of an .egg file
          classifiers=['Intended Audience :: Science/Research',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved',
                       'Programming Language :: Python',
                       'Topic :: Software Development',
                       'Topic :: Scientific/Engineering',
                       'Operating System :: Microsoft :: Windows',
                       'Operating System :: POSIX',
                       'Operating System :: Unix',
                       'Operating System :: MacOS'],
          platforms='any',
          packages=package_tree(DISTNAME),
    )