from setuptools import setup

setup(name="fakevnc",
    version="0.2",
    description="Fake VNC Server",
    long_description="""
    """,
    download_url="http://github.com/JustinAzoff/fakevnc/tree/master",
    license='MIT',
    classifiers=[
        "Topic :: System :: Networking",
        "Environment :: Console",
    ],
    keywords='VNC',
    author="Justin Azoff",
    author_email="JAzoff@uamail.albany.edu",
    py_modules = ["fakevnc"], 
    install_requires=[
        "twisted"
    ],
    entry_points = {
        'console_scripts': [
            'fakevnc   = fakevnc:main',
        ]
    },
)
