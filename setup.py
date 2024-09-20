from setuptools import setup, find_packages

setup(
    name="ci_manager",
    version="1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            ci-manager='ci_manager.ci_manager_cli:main',
            ci-setup='ci_manager.ci_setup_cli:main'
        ],
    },
    install_requires=[
        colorama
    ],
    data_files=[
        ('/etc/ci-manager')
    ]
)
    