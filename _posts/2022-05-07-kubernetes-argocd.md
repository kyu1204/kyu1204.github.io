---
title: Kubernetes cloud에 ArgoCD배포하기
description: GitOps CD 툴인 ArgoCD를 kubernetes 클러스터에 설치하고 초기 설정하는 과정을 정리했습니다.
categories: [kubernetes, argocd]
tags: [cloud, kubernetes, argocd, devops, ci/cd]
image: cover-argo.jpeg
date: 2022-05-07 00:00:00 +09:00
img_path: /assets/img/argocd/
---

## 개요

ArgoCD 는 GitOps 로 설정한 레포지토리의 YAML 파일을 쿠버네티스에 배포해주는 CD 툴 입니다. 자세한 내용은 [이곳](https://argoproj.github.io/cd/)을 참조해 주세요. <br>
이번 핸즈온에서는 ArgoCD 배포 및 초기 설정, git repo 연결까지 진행해보겠습니다.

핸즈온 순서는 다음과 같습니다.

> 1. Prerequisite
> 2. ArgoCD yaml install
> 3. ArgoCD Setting

클러스터 사양은 다음과 같으며, kubernetes cluster 가 배포중이여야 합니다.

> kubernetes 배포 관련 문서는 [이곳](https://kyu1204.github.io/2022/04/21/kubespray.html)을 참조해주세요.

> HOST: 3 (kubernetes cluster)  
> OS: Ubuntu 20.04  
> vCPU: 8  
> RAM: 16G  
> HDD: vda: 50G, vdb: 100G (OSD 용)  
> Network: 10.10.0.59, 10.10.0.4, 10.10.0.20

## Prerequisite

### Git Repository 준비 (Github)

![Image](20220507162837.png)
![Image](20220507165903.png)

## Install

### Create Namespace

```shell
kubectl create namespace argocd
```

### ArgoCD Yaml Apply (Non HA)

```shell
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### ArgoCD Yaml Apply (HA)

```shell
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/ha/install.yaml
```

### 설치 확인

```shell
kubectl get all -n argocd

NAME                                                    READY   STATUS    RESTARTS     AGE
pod/argocd-application-controller-0                     1/1     Running   1 (8d ago)   23d
pod/argocd-applicationset-controller-79f97597cb-wlhtw   1/1     Running   0            23d
pod/argocd-dex-server-6fd8b59f5b-znt4w                  1/1     Running   0            23d
pod/argocd-notifications-controller-5549f47758-7z22t    1/1     Running   0            23d
pod/argocd-redis-79bdbdf78f-wzpw9                       1/1     Running   0            23d
pod/argocd-repo-server-6b7bf55d9d-xj65t                 1/1     Running   1 (8d ago)   11d
pod/argocd-server-664b7c6878-8vrz2                      1/1     Running   1 (8d ago)   23d

NAME                                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/argocd-applicationset-controller          ClusterIP   10.101.226.54    <none>        7000/TCP                     23d
service/argocd-dex-server                         ClusterIP   10.109.39.44     <none>        5556/TCP,5557/TCP,5558/TCP   23d
service/argocd-metrics                            ClusterIP   10.108.108.134   <none>        8082/TCP                     23d
service/argocd-notifications-controller-metrics   ClusterIP   10.105.183.243   <none>        9001/TCP                     23d
service/argocd-redis                              ClusterIP   10.101.249.156   <none>        6379/TCP                     23d
service/argocd-repo-server                        ClusterIP   10.107.19.255    <none>        8081/TCP,8084/TCP            23d
service/argocd-server                             NodePort    10.97.84.246     <none>        80:30269/TCP,443:32042/TCP   23d
service/argocd-server-metrics                     ClusterIP   10.105.63.51     <none>        8083/TCP                     23d

NAME                                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/argocd-applicationset-controller   1/1     1            1           23d
deployment.apps/argocd-dex-server                  1/1     1            1           23d
deployment.apps/argocd-notifications-controller    1/1     1            1           23d
deployment.apps/argocd-redis                       1/1     1            1           23d
deployment.apps/argocd-repo-server                 1/1     1            1           23d
deployment.apps/argocd-server                      1/1     1            1           23d

NAME                                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/argocd-applicationset-controller-79f97597cb   1         1         1       23d
replicaset.apps/argocd-dex-server-6fd8b59f5b                  1         1         1       23d
replicaset.apps/argocd-notifications-controller-5549f47758    1         1         1       23d
replicaset.apps/argocd-redis-79bdbdf78f                       1         1         1       23d
replicaset.apps/argocd-repo-server-5569c7b657                 0         0         0       23d
replicaset.apps/argocd-repo-server-6b7bf55d9d                 1         1         1       11d
replicaset.apps/argocd-server-664b7c6878                      1         1         1       23d

NAME                                             READY   AGE
statefulset.apps/argocd-application-controller   1/1     23d
```

### Service NodePort 변경

```shell
kubectl patch svc -n argocd argocd-server -p '{"spec": {"type": "NodePort"}}'
```

### 초기 비밀번호 확인

```shell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

### 사이트 확인 & 로그인

![Image](20220507182024.png)

### Git repo 연결

**Settings -> Repositories -> CONNECT REPO USING HTTPS**
![Image](20220507182420.png)

![Image](20220507182651.png)

![Image](20220507182736.png)

## Test

### YAML 파일 작성 (Git Repo)

`db/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  labels:
    app: db
spec:
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
        - name: postgres
          image: postgres:latest
          env:
            - name: POSTGRES_USER
              vaule: "postgres"
            - name: POSTGRES_PASSWORD
              value: "postgres"
            - name: PGDATA
              value: "/var/lib/postgresql/data/k8s"
          ports:
            - containerPort: 5432
              protocol: TCP
          volumeMounts:
            - name: volume
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: volume
          persistentVolumeClaim:
            claimName: db-pvc
```

`db/pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20G
  storageClassName: rook-ceph-block
```

`db/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  labels:
    app: db
spec:
  type: NodePort
  ports:
    - port: 5432
      protocol: TCP
  selector:
    app: db
```

`kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - pvc.yaml
  - service.yaml
  - deployment.yaml
```

### ArgoCD App 생성

![Image](20220507190854.png)
![Image](20220507191118.png)
![Image](20220507191158.png)
![Image](20220507191333.png)
![Image](20220507191540.png)

## 마치며

CD 툴인 ArgoCD 를 kubernetes cluster 위에 배포, Git Repo 연결을 통해 kubernetes YAML 배포까지 진행해 봤습니다. 오늘 작성한 샘플 YAML 은 [이곳](https://github.com/kyu1204/argocd_resource)에 있습니다. 다음은 Vault + argocd-vault plugin 을 통해 배포 시점에 Vault 연동을 통한 secret 데이터 바인딩을 진행해보겠습니다.

## Reference

- https://argo-cd.readthedocs.io/en/stable/#getting-started
- https://github.com/argoproj/argo-cd/releases?q=stable&expanded=true
- https://velog.io/@airoasis/ArgoCD-Kubernetes-Deployment
