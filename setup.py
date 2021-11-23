from setuptools import setup, find_packages

setup(
    name="indico-toolkit",
    version="1.1.0",
    packages=find_packages(exclude=["tests"]),
    description="""Tools to assist with Indico IPA development""",
    license="MIT License (See LICENSE)",
    author="indico",
    author_email="engineering@indico.io",
    tests_require=["pytest>=5.2.1", "requests-mock>=1.7.0-7", "pytest-dependency==0.5.1"],
    install_requires=[
        "indico-client>=4.9.0",
        "numpy>=1.16.0",
        "Pillow>=6.2.0",
        "requests>=2.22.0",
        "setuptools>=41.4.0",
        "pandas>=1.0.3",
        "coverage>=5.5",
        "PyMuPDF==1.18.13",
        "plotly==5.2.1"
    ],
)
