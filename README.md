# Cilium Kubernetes Cluster Setup

VirtualBox와 Vagrant를 사용하여 로컬 환경에 Kubernetes 1.34.2 클러스터를 구축하고, Cilium v1.16.5를 네트워크 플러그인으로 설정하는 자동화 프로젝트입니다.

## 개요

이 프로젝트는 다음을 제공합니다:

- **인프라**: VirtualBox + Vagrant를 통한 VM 자동 프로비저닝 (1 Master + 2 Worker 노드)
- **Kubernetes**: Kubespray를 통한 Kubernetes 1.34.2 클러스터 자동 배포
- **네트워킹**: Cilium v1.16.5 CNI 플러그인 (eBPF 기반)
- **보안**: Network Policy 기반 보안, WireGuard 암호화
- **관찰성**: Hubble UI를 통한 실시간 네트워크 플로우 모니터링
- **모니터링**: Prometheus + Grafana 메트릭 수집 및 시각화

## 아키텍처

\\\

                      Host Machine                            
            
     Master         Worker-1        Worker-2          
   192.168.56.10  192.168.56.11   192.168.56.12       
    4GB / 2CPU      3GB / 2CPU      3GB / 2CPU        
            
                       
              192.168.56.0/24 (Host-Only)                     

                           
                    Cilium CNI (eBPF)
                           
        
                                            
   Pod Network      Service Network    Hubble UI
  10.244.0.0/16     10.96.0.0/12      (NodePort)
\\\

## 사전 요구사항

### 필수 소프트웨어

- **VirtualBox** >= 6.1
- **Vagrant** >= 2.0
- **Python** >= 3.8
- **Git**

### 시스템 리소스

- **RAM**: 최소 10GB 여유 공간
- **Disk**: 최소 50GB 여유 공간
- **CPU**: 멀티코어 프로세서 권장
- **네트워크**: 192.168.56.0/24 대역 사용 가능

## 빠른 시작

### 1. 리포지토리 클론

\\\ash
git clone https://github.com/zapan1015/kubespray_cilium.git
cd kubespray_cilium
\\\

### 2. Python 가상 환경 설정

\\\ash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
\\\

### 3. VM 프로비저닝

\\\ash
cd vagrant
vagrant up
\\\

### 4. Kubernetes 클러스터 배포

\\\ash
cd ../kubespray
ansible-playbook -i inventory/mycluster/hosts.yaml cluster.yml
\\\

### 5. 클러스터 접근

\\\ash
export KUBECONFIG=\C:\Users\zapan/.kube/config
kubectl get nodes
\\\

## 주요 기능

### Cilium CNI

- **eBPF 기반 네트워킹**: 커널 레벨에서 고성능 패킷 처리
- **kube-proxy 대체**: eBPF를 통한 서비스 로드 밸런싱
- **IPAM**: Kubernetes 네이티브 IP 주소 관리
- **터널 모드**: VXLAN, Geneve, Direct Routing 지원

### Network Policy

- **L3/L4 정책**: IP 및 포트 기반 트래픽 제어
- **L7 정책**: HTTP 메서드, 경로 기반 필터링
- **Ingress/Egress**: 양방향 트래픽 정책 지원

### WireGuard 암호화

- **노드 간 암호화**: Pod-to-Pod 통신 보안
- **자동 키 관리**: WireGuard 키 페어 자동 생성 및 배포

### Hubble 관찰성

- **실시간 플로우 모니터링**: 네트워크 트래픽 시각화
- **Service Map**: 서비스 간 의존성 그래프
- **DNS/HTTP 추적**: L7 프로토콜 가시성
- **Web UI**: http://192.168.56.10:31234

### 모니터링

- **Prometheus**: Cilium 메트릭 수집
- **Grafana**: 대시보드 시각화
- **주요 메트릭**:
  - cilium_endpoint_count
  - cilium_policy_count
  - cilium_drop_count_total
  - hubble_flows_processed_total

## 프로젝트 구조

\\\
kubespray_cilium/
 .kiro/
    specs/
        cilium-k8s-cluster-setup/
            requirements.md    # 요구사항 문서
            design.md          # 설계 문서
            tasks.md           # 구현 작업 목록
 vagrant/
    Vagrantfile               # VM 구성
 kubespray/
    inventory/
        mycluster/
            hosts.yaml        # 노드 인벤토리
            group_vars/       # 클러스터 설정
 scripts/                      # 자동화 스크립트
 manifests/                    # Kubernetes 매니페스트
 README.md
\\\

## 구성 커스터마이징

### VM 리소스 변경

\agrant/Vagrantfile\에서 메모리 및 CPU 설정 수정:

\\\uby
vb.memory = "4096"  # Master 노드 RAM
vb.cpus = 2         # Master 노드 CPU
\\\

### Cilium 설정 변경

\kubespray/inventory/mycluster/group_vars/k8s_cluster/k8s-net-cilium.yml\:

\\\yaml
cilium_version: "v1.16.5"
cilium_tunnel_mode: "vxlan"  # vxlan, geneve, disabled
cilium_encryption_enabled: true
cilium_encryption_type: "wireguard"
\\\

### Network Policy 예제

\\\yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-http
spec:
  endpointSelector:
    matchLabels:
      app: web
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: client
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
\\\

## 검증 및 테스트

### 클러스터 상태 확인

\\\ash
# 노드 상태
kubectl get nodes -o wide

# Cilium 상태
cilium status

# Hubble 플로우 관찰
hubble observe --namespace default
\\\

### 테스트 애플리케이션 배포

\\\ash
kubectl create namespace test
kubectl run nginx --image=nginx --namespace=test
kubectl expose pod nginx --port=80 --namespace=test
\\\

### Network Policy 테스트

\\\ash
# 클라이언트 파드 생성
kubectl run client --image=busybox --command -- sleep 3600 -n test

# 연결 테스트
kubectl exec -n test client -- wget -q -O- http://nginx
\\\

## 트러블슈팅

### VM 생성 실패

\\\ash
# VM 상태 확인
vagrant status

# VM 재생성
vagrant destroy -f
vagrant up
\\\

### Cilium Agent 오류

\\\ash
# Cilium 로그 확인
kubectl logs -n kube-system -l k8s-app=cilium

# Cilium 재시작
kubectl rollout restart ds/cilium -n kube-system
\\\

### 네트워크 연결 문제

\\\ash
# Cilium 연결성 테스트
cilium connectivity test

# Hubble로 드롭된 패킷 확인
hubble observe --verdict DROPPED
\\\

## 클린업

### 클러스터 제거

\\\ash
# Kubernetes 클러스터 제거
cd kubespray
ansible-playbook -i inventory/mycluster/hosts.yaml reset.yml

# VM 제거
cd ../vagrant
vagrant destroy -f
\\\

## 고급 기능

### Cilium Ingress Controller

\\\yaml
# Ingress 리소스 예제
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
spec:
  ingressClassName: cilium
  rules:
  - host: example.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: example-service
            port:
              number: 80
\\\

### Service Mesh 기능

Cilium의 L7 프로토콜 인식을 활용한 고급 트래픽 관리:

\\\yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: l7-http-policy
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/.*"
\\\

## HA 및 프로덕션 고려사항

현재 구성은 단일 Master 노드로 개발/테스트 환경에 적합합니다. 프로덕션 환경을 위해서는:

- **Multi-Master 구성**: etcd 및 control plane 고가용성
- **외부 etcd**: 별도 etcd 클러스터 구성
- **로드 밸런서**: API 서버 앞단 로드 밸런서
- **백업 전략**: etcd 정기 백업 및 복구 절차
- **모니터링 강화**: AlertManager 및 알림 설정

## 참고 자료

- [Cilium Documentation](https://docs.cilium.io/)
- [Kubespray Documentation](https://kubespray.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Hubble Documentation](https://docs.cilium.io/en/stable/gettingstarted/hubble/)
- [WireGuard](https://www.wireguard.com/)

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 작성자

zapan1015

## 버전

- **Kubernetes**: 1.34.2
- **Cilium**: 1.16.5
- **Kubespray**: 2.26
- **Ubuntu**: 22.04 LTS (Jammy Jellyfish)
