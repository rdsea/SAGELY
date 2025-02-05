# Problems

- Need to run as sudo when following happens:

```bash
Traceback (most recent call last):
  File "classify_image.py", line 40, in <module>
    from pycoral.utils.edgetpu import make_interpreter
  File "/home/aaltosea/RunningExample/new_object_classification/src/inference_coral/.venv/lib/python3.8/site-packages/pycoral/utils/edgetpu.py", line 24, in <module>
    from pycoral.pybind._pywrap_coral import GetRuntimeVersion as get_runtime_version
ImportError: /lib/aarch64-linux-gnu/libm.so.6: version `GLIBC_2.29' not found (required by /home/aaltosea/RunningExample/new_object_classification/src/inference_coral/.venv/lib/python3.8/site-packages/pycoral/pybind/_pywrap_coral.cpython-38-aarch64-linux-gnu.so
```
