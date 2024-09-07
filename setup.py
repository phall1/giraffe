from setuptools import setup, find_packages

setup(
    name="giraffes_can_speak",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        # List your dependencies here
    ],
    entry_points={
        'console_scripts': [
            'giraffes_can_speak=giraffes_can_speak.cli:main',
        ],
    },
)