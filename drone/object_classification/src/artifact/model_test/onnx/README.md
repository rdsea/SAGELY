# Base image

- We need different base image as we have three generations of jetson edge and each have its different jetpack
- Base image l4t-CUDA only have CUDA preinstalled, if we need to use cuDNN, we need to installed it manually inside the image or use TensorRT image

# Running profiling image:
- You need to mount the dataset to /accuracy\_profiling/data  and the results directory in host to /accuracy\_profiling/results
```bash
sudo docker run -v ./val_images/:/accuracy_profiling/data --gpus all -v /mnt/sd_card/git/RunningExample/new_object_classification/src/artifact/model_test/onnx/results/:/accuracy_profiling/results rdsea/onnx_accuracy_profiling:All
```
