# Testing inference service

1. Create onnx model

- Install required libs

```bash
pip install -r /artifact/model_test/onnx/create_onnx_requirements.txt
```

- Run python script to create onnx model

```bash
cd artifact/model_test/onnx
mkdir onnx_model
python3 create_onnx_model.py
```

2. Download imagenet:
   Two ways:

- Download the imagenet dataset from Google drive and extract it to new_object_classification artifact/dataset/imagenet/data/
- Download from remote server:

```bash
rsync -r aaltosea@edge-raspi1.cs.aalto.fi:/home/aaltosea/RunningExample/new_object_classification/src/artifact/dataset/imagenet/data/val_images $your_local_destination
```

3. Move onnx_model to the inference model

```bash
mv ./artifact/model_test/onnx/onnx_model ./inference
```

or download it to src/inference/onnx_model with:

```bash
rsync -r aaltosea@edge-jetxavier1.cs.aalto.fi:/mnt/sd_card/git/RunningExample/new_object_classification/src/artifact/model_test/onnx/onnx_model/ ./onnx_model
```

4. Run the inference service

- Run the server by following. Add --debug flag for auto-reload during development

```bash
cd inference
inference/run_server.sh
```

> [!NOTE]
>
> The default model is MobileNet, change CHOSEN_MODEL in run_server.sh to other model if you want to change the used model

5. Run the client

```bash
cd /client
python3 client_inference.py --rate 10
```

- The default rate is 15
