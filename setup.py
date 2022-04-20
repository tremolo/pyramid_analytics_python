from setuptools import setup
setup(
    name='pyramid_analytics_api',
    author='Shawn Sarwar',
    author_email="shawn.sarwar@pyramidanalytics.com",
    description='''Pyramid Analytics REST APIs in Python''',
    version='1.1.0',
    packages=['pyramid_api'],
    setup_requires=['pytest','pytest-runner', 'requests'],
    url='https://github.com/shawnsarwar/pyramid_analytics_api',
    keywords=['REST', 'pyramidanalytics', 'pyramid', 'analytics'],
    classifiers=[]
)
