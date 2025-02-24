from setuptools import find_packages, setup

package_name = "client_drone"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/drone_launch.py"]),
    ],
    install_requires=[
        "setuptools",
        "requests",
        "yaml",
        "os",
        "random",
        "Timer",
        "aiohttp",
        "ClientConnectorError",
        "asyncio",
    ],
    zip_safe=True,
    maintainer="nguyent141",
    maintainer_email="tringuyennht@gmail.com",
    description="TODO: Package description",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "sensor_publisher = client_drone.sensor_publisher:main",
            "client = client_drone.client:main",
            "drone_data_sender = client_drone.drone_data_sender:main",
        ],
    },
)
