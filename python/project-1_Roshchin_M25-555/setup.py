from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()


setup(
    name="labyrinth_game",
    version="0.1.0",
    author="Philipp Roschin",
    author_email="r.phil@yandex.ru",
    description="Labyrinth game.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "labyrinth_game=labyrinth_game.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
)
