from setuptools import find_packages, setup

package_name = 'actuator_node'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Yunpeng Yang',
    maintainer_email='yangyunpeng@gmail.com',
    description='Actuator node — e-stop GPIO 25 polling, motor PWM scaffolding',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'actuator_node = actuator_node.actuator_node:main',
        ],
    },
)
