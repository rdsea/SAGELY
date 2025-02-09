# What do you can do?
[this link](https://istio.io/latest/docs/tasks/observability/distributed-tracing/jaeger/)

- Jaeger for istio
> kubectl apply -f jaeger-istio.yml

- application
> ...

- extension provider referring to the jaeger collector service
> istioctl install -f tracing.yml --skip-confirmation

- enable tracing
> kubectl apply -f enable_tracing.yml

- view dashboard
> istioctl dashboard jaeger
<!-- ## Config Istio tracing settings -->
<!-- - apply the IstioOperator if the current profile does not detail on it -->
<!-- > kubectl apply -f Istio-operator.yml -->
