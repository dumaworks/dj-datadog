import os
import sys
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

reqs = ['datadog==0.12.0', 'six', 'psutil==4.4.2']

if [sys.version_info[0], sys.version_info[1]] < [2, 7]:
    reqs.append("simplejson>=2.0.9")

setup(
    name='dj_datadog',
    version='0.1.2',
    packages=['dj_datadog'],
    include_package_data=True,
    license='BSD',
    description=('A simple Django middleware for submitting '
                 'timings and exceptions to Datadog.'),
    long_description=README,
    author='Conor Branagan',
    author_email='conor.branagan@gmail.com',
    maintainer="Kenny Rachuonyo",
    maintainer_email="kenny.rachuonyo@gmail.com",
    install_requires=reqs
)
