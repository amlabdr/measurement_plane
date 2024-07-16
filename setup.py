from setuptools import setup, find_packages

setup(
    name="measurement_plane",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-dateutil",
        "python-qpid-proton==0.39.0"
    ],
    entry_points={
        'console_scripts': [
            'start-agent=measurement_plane.start_agent:start_agent',
        ],
    },
    include_package_data=True,
    description="A description of your project.",
    long_description="This is a long description of the measurement_plane project.",
    long_description_content_type="text/markdown",
    url="https://github.com/amlabdr/measurement_plane",
    author="amlabdr",
    author_email="amlabdr@example.com",  # Replace with your actual email
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)