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
        ("share/" + package_name + "/config", ["config/client_config.yaml"]),
    ],
    install_requires=[
        "setuptools",
        "requests",
        "PyYAML",
        "aiohttp",
        "pymavlink",
        "etcd3",
        "pydantic",
    ],
    zip_safe=True,
    maintainer="nguyent141",
    maintainer_email="tringuyennht@gmail.com",
    description="todo: package description",
    license="apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "client = client_drone.client:main",
            "receive_ftp_write_opa = client_drone.receive_ftp:main",
        ],
    },
)
