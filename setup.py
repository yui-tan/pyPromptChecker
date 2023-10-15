from setuptools import setup, find_packages

setup(
    name='pyPromptChecker',
    version='2.2.0',
    discription=' A small script for AI images created by stable diffusion webui ',
    author='Yui-tan',
    packages=find_packages(where='pyPromptChecker'),
    package_dir={'': 'pyPromptChecker'},
    install_requires=[
        'pyQt6',
        'pypng',
        'pillow',
        'pyqtdarktheme',
        'onnxruntime',
        'numpy',
        'opencv-python',
        'huggingface_hub'
    ],
    entry_points={
        'console_scripts': [
            'mikkumiku = main:main'
        ]
    }
)
