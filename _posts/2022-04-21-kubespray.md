---
title: Kubespray 를 이용한 kubernetes 배포
description: Ansible 기반 Kubespray로 HA 구성이 포함된 kubernetes 클러스터를 배포하는 과정을 단계별로 정리했습니다.
categories: [kubernetes]
tags: [cloud, kubernetes, ansible, kubespray]
image: /assets/img/k8s.png
date: 2022-04-21 00:00:00 +09:00
---

## 개요

ansible 을 활용하여 kubernetes 배포를 진행하는 프로젝트 입니다. 자세한 내용은 [이곳](https://github.com/kubernetes-sigs/kubespray)을 확인해주세요.<br>
kubespray 로 배포한 kubernetes cloud 는 nginx proxy 를 이용해 자체 HA로 구성되어 있어 별도의 HA 구성을 하지않아도 자동으로 구성됩니다.<br><br>
핸즈온 순서는 다음과 같습니다.<br>

> 1.  의존성 패키지 설치 및 ssh 설정
> 2.  kubespray git clone
> 3.  ansible inventory 생성
> 4.  ping 테스트
> 5.  playbook 실행

<br>클러스터의 사양은 다음과 같습니다.

> HOST: 3 (All Master, All Worker)  
> OS: Ubuntu 20.04  
> vCPU: 8  
> RAM: 16G  
> HDD: vda: 50G, vdb: 100G  
> Network: 10.10.0.59, 10.10.0.4, 10.10.0.20

## Prerequisite

### python3 의존성 패키지 설치

```bash
apt update && apt install -y python3-dev python3-pip gcc make
```

### git clone

```bash
git clone https://github.com/kubernetes-sigs/kubespray.git
```

### Requirements Install

```bash
cd kubespray
pip3 install -r requirements.txt
```

### ansible version 확인

```bash
ansible --version

ansible [core 2.12.3]
  config file = None
  configured module search path = ['/root/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/local/lib/python3.8/
  ...
```

### ssh setting

```bash
ssh-keygen -t rsa
for i in 59 4 20;do ssh-copy-id root@10.10.0.$i;done
```

## Inventory 설정 및 kubernetes 버전 확인

### sample 복사

```bash
cp -rfp inventory/sample inventory/mycluster
```

### inventory builder을 이용해 inventory 생성

```bash
declare -a IPS=(10.10.0.59 10.10.0.4 10.10.0.20)

CONFIG_FILE=inventory/mycluster/hosts.yaml python3 contrib/inventory_builder/inventory.py ${IPS[@]}
```

### inventory 수정

`inventory/mycluster/hosts.yaml`

```yaml
all:
  hosts:
    node1:
      ansible_host: 10.10.0.59
      ip: 10.10.0.59
      access_ip: 10.10.0.59
    node2:
      ansible_host: 10.10.0.4
      ip: 10.10.0.4
      access_ip: 10.10.0.4
    node3:
      ansible_host: 10.10.0.20
      ip: 10.10.0.20
      access_ip: 10.10.0.20
  children:
    # All Master
    kube_control_plane:
      hosts:
        node1:
        node2:
        node3:
    # All Worker
    kube_node:
      hosts:
        node1:
        node2:
        node3:
    # All HA
    etcd:
      hosts:
        node1:
        node2:
        node3:
    k8s_cluster:
      children:
        kube_control_plane:
        kube_node:
    calico_rr:
      hosts: {}
```

### kubernetes 설치 버전 확인

> kuberspray에서 지원하는 버전은 [이곳](https://github.com/kubernetes-sigs/kubespray#requirements)을 확인해주세요.

```bash
cat inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml

...
## Change this to use another Kubernetes version, e.g. a current beta release
kube_version: v1.23.5
...
```

## Node Check

### ansible ping

```
ansible -m ping -i inventory/mycluster/hosts.yaml all -u root

node1 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
node3 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
node2 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
```

## Install

### ansible playbook 실행

```bash
ansible-playbook -i inventory/mycluster/hosts.yaml --become --become-user=root -u root cluster.yml
```

## Test

### kubernetes node check

```bash
kubectl get nodes -o wide

NAME    STATUS   ROLES                  AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION     CONTAINER-RUNTIME
node1   Ready    control-plane,master   4d    v1.23.5   10.10.0.59    <none>        Ubuntu 20.04.3 LTS   5.4.0-91-generic   containerd://1.6.2
node2   Ready    control-plane,master   4d    v1.23.5   10.10.0.4     <none>        Ubuntu 20.04.3 LTS   5.4.0-91-generic   containerd://1.6.2
node3   Ready    control-plane,master   4d    v1.23.5   10.10.0.20    <none>        Ubuntu 20.04.3 LTS   5.4.0-91-generic   containerd://1.6.2
```

### kubernetes core pod check

```bash
kubectl get all -n kube-system

NAME                                           READY   STATUS    RESTARTS         AGE
pod/calico-kube-controllers-75fcdd655b-zxdvq   1/1     Running   0                4d
pod/calico-node-t5qxw                          1/1     Running   0                4d
pod/calico-node-vq247                          1/1     Running   0                4d
pod/calico-node-zsb97                          1/1     Running   0                4d
pod/coredns-76b4fb4578-h6c42                   1/1     Running   0                4d
pod/coredns-76b4fb4578-qtj9w                   1/1     Running   0                4d
pod/dns-autoscaler-7979fb6659-bcvgd            1/1     Running   0                4d
pod/kube-apiserver-node1                       1/1     Running   0                4d
pod/kube-apiserver-node2                       1/1     Running   0                4d
pod/kube-apiserver-node3                       1/1     Running   0                4d
pod/kube-controller-manager-node1              1/1     Running   0                4d
pod/kube-controller-manager-node2              1/1     Running   0                4d
pod/kube-controller-manager-node3              1/1     Running   0                4d
pod/kube-proxy-hdnn9                           1/1     Running   0                4d
pod/kube-proxy-tcfp2                           1/1     Running   0                4d
pod/kube-proxy-z9w8h                           1/1     Running   0                4d
pod/kube-scheduler-node1                       1/1     Running   0                4d
pod/kube-scheduler-node2                       1/1     Running   0                4d
pod/kube-scheduler-node3                       1/1     Running   0                4d
pod/nodelocaldns-55dcs                         1/1     Running   0                4d
pod/nodelocaldns-66qrj                         1/1     Running   0                4d
pod/nodelocaldns-jl55r                         1/1     Running   0                4d

NAME              TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
service/coredns   ClusterIP   10.233.0.3   <none>        53/UDP,53/TCP,9153/TCP   4d

NAME                          DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
daemonset.apps/calico-node    3         3         3       3            3           kubernetes.io/os=linux   4d
daemonset.apps/kube-proxy     3         3         3       3            3           kubernetes.io/os=linux   4d
daemonset.apps/nodelocaldns   3         3         3       3            3           kubernetes.io/os=linux   4d

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/calico-kube-controllers   1/1     1            1           4d
deployment.apps/coredns                   2/2     2            2           4d
deployment.apps/dns-autoscaler            1/1     1            1           4d

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/calico-kube-controllers-75fcdd655b   1         1         1       4d
replicaset.apps/coredns-76b4fb4578                   2         2         2       4d
replicaset.apps/dns-autoscaler-7979fb6659            1         1         1       4d

```

## 마치며

kubespray 를 통한 kubernetes cloud 배포를 진행해봤는데, 확실히 ansible 을 더 공부하면 좋을 것 같다는 생각이 들었습니다. <br>
다음은 배포된 kubernetes 에 Rook 을 이용한 Ceph 배포 및 StroageClass 생성을 진행해보겠습니다.

## Reference

- https://github.com/kubernetes-sigs/kubespray
