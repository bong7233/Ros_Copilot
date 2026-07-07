from setuptools import find_packages, setup

package_name = 'copilot_agent'

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
    description='Layer 2 (brain): LLM agent calling ROS2-mapped tools.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'agent = copilot_agent.agent_node:main',
            'agent_cli = copilot_agent.agent_cli:main',
        ],
    },
)
