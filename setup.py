from setuptools import find_packages, setup

setup(
    name="pixBoards",
    version=2.6,
    packages=find_packages(),
    include_package_data=True,
    package_data={"pixBoards": ["templates/*.*"]},
    # install_requires = [
    # ]
    entry_points={
        "console_scripts": [
            "run=boards.cli:main",
        ],
    },
)

# python3 setup.py sdist bdist_wheel
