# Vagrant Configuration

이 디렉토리는 VirtualBox와 Vagrant를 사용한 VM 프로비저닝 구성을 포함합니다.

## 파일 구조

- `Vagrantfile` - VM 구성 정의 (Master 1개, Worker 2개)
- `provision.sh` - VM 기본 패키지 설치 스크립트

## VM 사양

### Master Node (192.168.56.10)
- RAM: 4GB
- CPU: 2 cores
- 역할: Kubernetes Control Plane, etcd

### Worker Nodes (192.168.56.11-12)
- RAM: 3GB
- CPU: 2 cores
- 역할: Kubernetes Worker Nodes

## 사용법

```bash
# VM 생성 및 시작
vagrant up

# VM 상태 확인
vagrant status

# SSH 접속
vagrant ssh master
vagrant ssh worker-1
vagrant ssh worker-2

# VM 중지
vagrant halt

# VM 삭제
vagrant destroy -f
```

## 네트워크 구성

- Host-Only Network: 192.168.56.0/24
- VM들은 호스트 머신과 서로 간 통신 가능
- 외부 인터넷 접속은 NAT를 통해 제공