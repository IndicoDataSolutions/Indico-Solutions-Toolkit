from setuptools import setup, find_packages

setup(
    name="indico-toolkit",
    version="2.0.1",
    packages=find_packages(exclude=["tests"]),
    description="""Tools to assist with Indico IPA development""",
    license="MIT License (See LICENSE)",
    author="indico",
    author_email="engineering@indico.io",
    tests_require=["pytest>=5.2.1", "requests-mock>=1.7.0-7", "pytest-dependency==0.5.1", "coverage>=5.5"],
    install_requires=[
        "indico-client==5.1.3",
        "plotly==5.2.1",
        "tqdm==4.50.0",
        "faker==13.3.3",
    ],
    extras_require = {
        "full": ["PyMuPDF==1.19.6"]
    }
)
