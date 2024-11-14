## Docker build for ros2
```bash

cd src/client_drone

docker build -t client_drone . 

docker run --network host -v <image_data_for_sending>:/root/client_drone/src/data/val_images --rm -it client_drone bash --
```
