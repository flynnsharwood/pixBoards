from setuptools import find_packages, setup

setup(
    name="pixBoards",
    version=2.5,
    packages=find_packages(),
    include_package_data=True,
    package_data={"pixBoards": ["templates/*.*"]},
    # install_requires = [
    # ]
)

# python3 setup.py sdist bdist_wheel
