from setuptools import setup, find_packages


setup(
    name="measurement_plane",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-qpid-proton==0.39.0",  # Required for AMQP
        "python-dateutil>=2.8.0",      # For date manipulation
        "jsonschema>=4.0.0",           # For JSON validation
        "numpy>=1.21.0",               # For numerical processing
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
    python_requires='>=3.6',
)