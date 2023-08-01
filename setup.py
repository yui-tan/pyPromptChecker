from setuptools import setup, find_packages

setup(
    name='pyPromptChecker',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'pyQt6',
        'pypng'
    ],
    entry_points={
        'console_scripts': [
            'mikkumiku = main:main'
        ]
    }
)