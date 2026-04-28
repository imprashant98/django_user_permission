from setuptools import setup, find_packages

setup(
    name='django-user-permissions',
    version='0.1.0',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    install_requires=[
        'Django>=3.2',
        'djangorestframework>=3.14',
    ],
    classifiers=[
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
    ],
)