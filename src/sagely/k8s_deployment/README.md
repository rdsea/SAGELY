## Installing k8s using kubeadm

- There is a lot of here and there bug but I have solved one by deleting `/etc/cni/net.d`, try to follow the kubeadm instruction
- Useful link:

  - [https://github.com/projectcalico/calico/issues/8694]

- Joining edge node

```bash
sudo keadm join --cloudcore-ipport="ip:10000" --token={token} --kubeedge-version=v1.17.0 --cgroupdriver=systemd
```

- Leave kubeedge cluster:
