import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'copilot_rag'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'data'), glob('data/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='bong',
    maintainer_email='batmantwo7233@gmail.com',
    description='Layer 1: RAG knowledge assistant exposed as a ROS2 service.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'query_server = copilot_rag.query_node:main',
            'ingest = copilot_rag.ingest:main',
            'ask = copilot_rag.ask:main',
        ],
    },
)
