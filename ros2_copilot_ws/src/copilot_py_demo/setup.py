from setuptools import find_packages, setup

package_name = 'copilot_py_demo'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='bong',
    maintainer_email='batmantwo7233@gmail.com',
    description='Phase 0: rclpy talker publishing Heartbeat.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'talker = copilot_py_demo.talker:main',
        ],
    },
)
