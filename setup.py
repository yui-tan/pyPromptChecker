from setuptools import setup, find_packages

setup(
    name='pyPromptChecker',
    version='1.0.0',
    packages=find_packages(),
    package_data={'pyPromptChecker': ['lib/*.py']},
    install_requires=[
        'pyQt6',
        'pypng',
        'pyexiv2'
    ],
    entry_points={
        'console_scripts': [
            'mikkumiku = pyPromptChecker.main:main'
        ]
    }
)
