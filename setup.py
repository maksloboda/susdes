from setuptools import setup

setup(
    name='susdes',
    version='0.1.1',
    py_modules=['main'],
    url="https://github.com/maksloboda/susdes",
    author="Maks Loboda",
    author_email="mloboda@edu.hse.ru",
    install_requires=[
        'click',
        'python-jenkins',
    ],
    license='MIT',
    entry_points={
        'console_scripts': [
            'susdes = susdes:cli',
        ],
    },
)
