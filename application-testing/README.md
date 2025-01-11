# application-testing

```bash
protoc --python_out=. example.proto

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# execute etcd like a database
./etcd 

# run
python server.py

python client1.py

python client-test2.py
```
