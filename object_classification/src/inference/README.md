# Build image

```bash
cd RunningExample/new_object_classification/src/
docker build --platform=linux/arm64/v8 -t rdsea/onnx_inference:cpu -f ./inference/Dockerfile.cpu .
```

# Problems encountered:

- Having both onnxruntime and onnxruntime_gpu can cause CUDA to not be recognizable
