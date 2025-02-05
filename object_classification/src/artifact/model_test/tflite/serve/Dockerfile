FROM python:3.10.14-slim-bullseye

WORKDIR /tflite_test_serve

RUN python3 -m pip install --no-cache-dir tflite-runtime==2.13.0 \ 
  fastapi==0.112.0\ 
  numpy==1.23.5 \ 
  uvicorn==0.31.5

COPY ./tflite_model/MobileNet.tflite ./tflite_model/MobileNet.tflite
COPY ./tflite_rest.py ./tflite_rest.py

EXPOSE 8000
CMD ["uvicorn", "tflite_rest:app"]
