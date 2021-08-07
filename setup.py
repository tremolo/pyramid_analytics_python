from setuptools import setup
setup(
    name='pyramid_analytics_api',
    author='Shawn Sarwar',
    author_email="shawn.sarwar@pyramidanalytics.com",
    description='''An wrapper around PA REST APIs''',
    version='1.0.0',
    packages=['pyramid_api'],
    # requires=['dataclasses-json', 'requests'],
    setup_requires=['pytest','pytest-runner', 'requests'],
    url='https://github.com/shawnsarwar/pyramid_analytics_api',
    keywords=['REST', 'pyramidanalytics', 'pyramid', 'analytics'],
    classifiers=[]
)
