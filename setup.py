from setuptools import setup, find_packages

setup(
    name='pyPromptChecker',
    version='2.2.0',
    packages=find_packages(),
    install_requires=[
        'pySide6',
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
            'mikkumiku = pyPromptChecker.main:main'
        ]
    }
)
