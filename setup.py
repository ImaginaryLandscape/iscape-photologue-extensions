from setuptools import setup, find_packages


setup(
    name='iscapephotologue',
    version='0.1.1',

    install_requires=(
        'django-photologue',
    ),

    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=('ez_setup', 'examples', 'tests')),
)
