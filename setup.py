from setuptools import setup, find_packages

setup(
    name="indico-toolkit",
    version="1.2.3",
    packages=find_packages(exclude=["tests"]),
    description="""Tools to assist with Indico IPA development""",
    license="MIT License (See LICENSE)",
    author="indico",
    author_email="engineering@indico.io",
    tests_require=["pytest>=5.2.1", "requests-mock>=1.7.0-7", "pytest-dependency==0.5.1", "coverage>=5.5"],
    install_requires=[
        "indico-client==4.9.0",
        "plotly==5.2.1",
        "tqdm==4.50.0"
    ],
    extras_require = {
        "full": ["PyMuPDF==1.19.6"]
    }
)
