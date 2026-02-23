# Automation Scripts

이 디렉토리는 클러스터 배포 및 관리를 위한 자동화 스크립트를 포함합니다.

## 스크립트 목록

### 환경 설정
- `setup_environment.py` - Python 가상 환경 및 의존성 설정
- `check_prerequisites.py` - 호스트 시스템 사전 요구사항 검증

### VM 관리
- `provision_vms.py` - VM 생성 및 프로비저닝 자동화 (예정)
- `verify_vms.py` - VM 상태 및 연결성 검증 (예정)

### 클러스터 배포
- `deploy_kubernetes.py` - Kubernetes 클러스터 배포 자동화 (예정)
- `install_cilium.py` - Cilium CNI 설치 및 구성 (예정)

### 모니터링 및 검증
- `verify_cluster.py` - 클러스터 상태 검증 (예정)
- `setup_monitoring.py` - Prometheus/Grafana 모니터링 스택 설정 (예정)

## 사용법

### 1. 환경 설정
```bash
# Python 가상 환경 설정
python scripts/setup_environment.py

# 가상 환경 활성화 (Windows)
activate.bat

# 사전 요구사항 확인
python scripts/check_prerequisites.py
```

### 2. 클러스터 배포
```bash
# VM 프로비저닝
python scripts/provision_vms.py

# Kubernetes 배포
python scripts/deploy_kubernetes.py

# Cilium 설치
python scripts/install_cilium.py
```

### 3. 검증 및 모니터링
```bash
# 클러스터 상태 확인
python scripts/verify_cluster.py

# 모니터링 스택 설정
python scripts/setup_monitoring.py
```

## 요구사항

- Python 3.8+
- 가상 환경 활성화 필수
- requirements.txt의 모든 의존성 설치 필요