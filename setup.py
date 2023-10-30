from setuptools import find_packages, setup

setup(
    name="indico-toolkit",
    version="6.0.0",
    packages=find_packages(exclude=["tests"]),
    description="""Tools to assist with Indico IPA development""",
    license="MIT License (See LICENSE)",
    author="indico",
    author_email="engineering@indico.io",
    tests_require=[
        "pytest>=5.2.1",
        "requests-mock>=1.7.0-7",
        "pytest-dependency==0.5.1",
    ],
    install_requires=[
        "indico-client>=5.1.4",
        "plotly==5.2.1",
        "tqdm==4.50.0",
        "faker==13.3.3",
        "python-dateutil==2.8.1"
    ],
    extras_require={"full": ["PyMuPDF==1.19.6", "spacy>=3.1.4,<4"]},
)
