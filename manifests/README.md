# Kubernetes Manifests

이 디렉토리는 Kubernetes 리소스 매니페스트 파일들을 포함합니다.

## 디렉토리 구조

```
manifests/
├── cilium/                 # Cilium 관련 매니페스트
│   ├── values.yaml        # Cilium Helm values
│   └── network-policies/  # Network Policy 예제
├── monitoring/            # 모니터링 스택
│   ├── prometheus/        # Prometheus 구성
│   └── grafana/          # Grafana 대시보드
├── test-apps/            # 테스트 애플리케이션
└── ingress/              # Ingress 리소스 예제
```

## 주요 매니페스트

### Cilium 구성
- `cilium/values.yaml` - Cilium Helm 차트 설정값
- `cilium/network-policies/` - L3/L4/L7 Network Policy 예제

### 모니터링
- `monitoring/prometheus/` - Prometheus 설정 및 ServiceMonitor
- `monitoring/grafana/` - Grafana 대시보드 ConfigMap

### 테스트 애플리케이션
- `test-apps/nginx.yaml` - 기본 웹 서버 테스트
- `test-apps/client.yaml` - 네트워크 연결 테스트용 클라이언트

### Ingress
- `ingress/example-ingress.yaml` - Cilium Ingress Controller 예제

## 사용법

```bash
# 매니페스트 적용
kubectl apply -f manifests/test-apps/

# Network Policy 적용
kubectl apply -f manifests/cilium/network-policies/

# 모니터링 스택 배포
kubectl apply -f manifests/monitoring/

# 리소스 확인
kubectl get all -n test
kubectl get ciliumnetworkpolicies
```

## 주의사항

- 매니페스트 적용 전 클러스터가 정상 동작하는지 확인
- Network Policy는 Cilium이 설치된 후에 적용
- 모니터링 스택은 충분한 리소스가 있는지 확인 후 배포