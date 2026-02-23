# Implementation Plan: Cilium Kubernetes Cluster Setup

## Overview

이 구현 계획은 VirtualBox와 Vagrant를 사용하여 Kubernetes 1.35.1 클러스터를 구축하고 Cilium v1.16.5 CNI를 설정하는 전체 프로세스를 다룹니다. 구현은 인프라 프로비저닝부터 클러스터 배포, 네트워크 설정, 모니터링 구성까지 순차적으로 진행되며, 각 단계는 이전 단계를 기반으로 구축됩니다. 모든 구성은 Infrastructure as Code 원칙을 따르며, Python 스크립트를 통해 자동화됩니다.

현재 상태: 프로젝트 구조와 문서만 존재하며, 실제 구현은 아직 시작되지 않았습니다.

## Tasks

- [ ] 1. 프로젝트 구조 및 사전 요구사항 검증 설정
  - 프로젝트 디렉토리 구조 생성 (vagrant/, kubespray/, scripts/, manifests/)
  - Python 가상 환경 설정 및 의존성 패키지 설치 (ansible, jinja2, pyyaml)
  - 호스트 시스템 리소스 검증 스크립트 작성 (RAM, Disk, VirtualBox, Vagrant 버전 확인)
  - requirements.txt 파일 생성
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 1.1 리소스 검증 로직에 대한 단위 테스트 작성
  - 리소스 부족 시나리오 테스트
  - VirtualBox/Vagrant 미설치 시나리오 테스트
  - _Requirements: 10.6_

- [ ] 2. Vagrantfile 및 VM 프로비저닝 스크립트 구현
  - [ ] 2.1 Vagrantfile 생성 및 VM 구성 정의
    - Master 노드 정의 (192.168.56.10, 4GB RAM, 2 CPU)
    - Worker 노드 2개 정의 (192.168.56.11-12, 3GB RAM, 2 CPU)
    - Host-only 네트워크 어댑터 구성 (192.168.56.0/24)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ] 2.2 VM 프로비저닝 셸 스크립트 작성
    - 기본 패키지 설치 (Docker, containerd, kubeadm 의존성)
    - SSH 키 배포 및 호스트명 설정
    - /etc/hosts 파일 구성
    - _Requirements: 1.8_

  - [ ] 2.3 Python 스크립트로 VM 생성 자동화
    - `vagrant up` 명령 실행 및 출력 모니터링
    - VM 상태 확인 및 네트워크 연결성 검증
    - _Requirements: 1.7, 11.1, 11.6_

- [ ] 2.4 VM 프로비저닝 검증 테스트 작성
  - 모든 VM이 실행 중인지 확인
  - 네트워크 연결성 테스트 (ping 테스트)
  - SSH 접근 가능 여부 확인
  - _Requirements: 1.7_

- [ ] 3. Checkpoint - VM 인프라 검증
  - Ensure all VMs are running and accessible, ask the user if questions arise.

- [ ] 4. Kubespray 인벤토리 및 구성 파일 생성
  - [ ] 4.1 Kubespray 저장소 클론 및 설정
    - Kubespray 저장소 클론 (특정 버전 태그)
    - Python 의존성 설치 (requirements.txt)
    - _Requirements: 2.1, 9.2_

  - [ ] 4.2 인벤토리 파일 생성 (hosts.yaml)
    - Jinja2 템플릿을 사용한 인벤토리 파일 생성
    - Master 노드를 kube_control_plane 및 etcd 그룹에 할당
    - Worker 노드를 kube_node 그룹에 할당
    - _Requirements: 2.2, 2.3, 2.5_

  - [ ] 4.3 클러스터 구성 파일 생성 (k8s-cluster.yml)
    - Kubernetes 버전 1.35.1 설정
    - CNI 플러그인을 cilium으로 설정
    - Pod CIDR (10.244.0.0/16) 및 Service CIDR (10.96.0.0/12) 설정
    - Container runtime을 containerd로 설정
    - _Requirements: 2.1, 3.4, 3.5_

  - [ ] 4.4 애드온 구성 파일 생성 (addons.yml)
    - Metrics Server 활성화
    - Helm 설치 활성화
    - _Requirements: 9.2_

- [ ] 4.5 구성 파일 검증 테스트 작성
  - YAML 구문 검증
  - 필수 필드 존재 여부 확인
  - IP 주소 및 CIDR 형식 검증
  - _Requirements: 9.6, 9.7_

- [ ] 5. Kubernetes 클러스터 배포 실행
  - [ ] 5.1 Ansible 플레이북 실행 스크립트 작성
    - `ansible-playbook cluster.yml` 실행 및 출력 로깅
    - 배포 진행 상황 모니터링
    - 오류 발생 시 로그 보존 및 보고
    - _Requirements: 2.1, 2.4, 11.2, 11.4_

  - [ ] 5.2 클러스터 배포 후 검증 스크립트 작성
    - kubectl 설정 및 클러스터 접근 확인
    - 모든 노드가 Ready 상태인지 확인
    - 시스템 파드가 Running 상태인지 확인
    - _Requirements: 2.8, 8.1, 8.2_

  - [ ] 5.3 kubeconfig 파일 복사 및 환경 변수 설정
    - Master 노드에서 kubeconfig 파일 복사
    - KUBECONFIG 환경 변수 설정
    - _Requirements: 2.7_

- [ ] 5.4 클러스터 배포 검증 테스트 작성
  - 노드 상태 확인 테스트
  - API 서버 접근 가능 여부 테스트
  - 인증서 유효성 검증
  - _Requirements: 2.6, 8.1_

- [ ] 6. Checkpoint - Kubernetes 클러스터 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Cilium CNI 설치 및 구성
  - [ ] 7.1 Cilium Helm values 파일 생성
    - Cilium 버전 1.16.5 설정
    - IPAM 모드를 kubernetes로 설정
    - kube-proxy 대체 활성화
    - API 서버 주소 설정 (192.168.56.10:6443)
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 7.2 Cilium Helm 차트 설치 스크립트 작성
    - Helm 저장소 추가 (cilium/cilium)
    - `helm install cilium` 명령 실행
    - 설치 상태 모니터링
    - _Requirements: 3.1, 11.3_

  - [ ] 7.3 Cilium 상태 검증 스크립트 작성
    - `cilium status` 명령 실행 및 파싱
    - 모든 노드에서 Cilium Agent 실행 확인
    - eBPF 프로그램 로드 확인
    - _Requirements: 3.6, 3.9, 8.3_

  - [ ] 7.4 테스트 파드 생성 및 IP 할당 검증
    - 테스트 파드 배포 (nginx)
    - Pod IP가 10.244.0.0/16 범위 내인지 확인
    - IP 할당 시간 측정 (5초 이내)
    - _Requirements: 3.7, 3.8, 8.6_

- [ ] 7.5 Cilium CNI 기능 검증 테스트 작성
  - Pod 네트워크 인터페이스 생성 확인
  - IP 할당 성능 테스트
  - eBPF 프로그램 로드 상태 확인
  - _Requirements: 3.6, 3.7, 3.8, 3.9_

- [ ] 8. WireGuard 암호화 구성
  - [ ] 8.1 Cilium 암호화 설정 업데이트
    - Helm values에 encryption.enabled=true 추가
    - encryption.type=wireguard 설정
    - Cilium 업그레이드 실행
    - _Requirements: 5.1_

  - [ ] 8.2 WireGuard 터널 상태 검증 스크립트 작성
    - WireGuard 키 페어 생성 확인
    - 노드 간 터널 상태 확인
    - 암호화된 트래픽 검증
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 9.1_

- [ ] 8.3 WireGuard 암호화 검증 테스트 작성
  - 터널 연결 상태 테스트
  - 암호화 키 교환 확인
  - 터널 실패 시 재연결 테스트
  - _Requirements: 5.6, 9.1_

- [ ] 9. Network Policy 구현 및 테스트
  - [ ] 9.1 샘플 Network Policy 매니페스트 작성
    - L3/L4 정책 예제 (특정 포트 허용/차단)
    - L7 HTTP 정책 예제 (경로 기반 필터링)
    - Ingress 및 Egress 정책 조합
    - _Requirements: 4.1, 4.2, 4.3, 4.8, 9.4_

  - [ ] 9.2 Network Policy 적용 및 검증 스크립트 작성
    - Policy 적용 (`kubectl apply`)
    - Policy 적용 시간 측정 (10초 이내)
    - 트래픽 차단/허용 동작 검증
    - _Requirements: 4.4, 4.5, 4.6_

  - [ ] 9.3 Policy 우선순위 테스트 시나리오 구현
    - 여러 정책이 겹치는 경우 테스트
    - 가장 구체적인 정책이 적용되는지 확인
    - _Requirements: 4.7_

- [ ] 9.4 Network Policy 검증 테스트 작성
  - Policy 파싱 및 검증 테스트
  - 트래픽 차단 로그 확인
  - L7 정책 적용 확인
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [ ] 10. Checkpoint - 네트워크 및 보안 기능 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Hubble Observability 플랫폼 구성
  - [ ] 11.1 Hubble 활성화 및 배포
    - Helm values에 hubble.enabled=true 추가
    - hubble.relay.enabled=true 설정
    - hubble.ui.enabled=true 설정
    - Cilium 업그레이드 실행
    - _Requirements: 6.1, 6.2_

  - [ ] 11.2 Hubble UI NodePort 서비스 구성
    - NodePort를 31234로 설정
    - 서비스 접근 가능 여부 확인
    - _Requirements: 6.2, 8.5_

  - [ ] 11.3 Hubble 플로우 데이터 수집 검증
    - 테스트 트래픽 생성 (pod-to-pod 통신)
    - Hubble CLI로 플로우 데이터 조회
    - gRPC API 접근 확인 (포트 4245)
    - _Requirements: 6.3, 6.4_

  - [ ] 11.4 Hubble UI 기능 검증 스크립트 작성
    - Service Map 표시 확인
    - 플로우 데이터 필터링 테스트 (namespace, pod, protocol, verdict)
    - Network Policy 적용 상태 표시 확인
    - _Requirements: 6.5, 6.6, 6.7, 6.8_

  - [ ] 11.5 L7 가시성 구성 및 검증
    - DNS 쿼리 캡처 확인
    - HTTP 요청 캡처 확인 (method, path, status code)
    - _Requirements: 6.9, 6.10_

- [ ] 11.6 Hubble 관찰성 검증 테스트 작성
  - Hubble Relay 접근 가능 여부 테스트
  - 플로우 데이터 수집 및 파싱 테스트
  - UI 렌더링 확인
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_

- [ ] 12. Prometheus 및 Grafana 모니터링 스택 배포
  - [ ] 12.1 Prometheus Operator 설치
    - Helm을 통한 kube-prometheus-stack 설치
    - Prometheus 서비스 구성
    - _Requirements: 7.1_

  - [ ] 12.2 Cilium ServiceMonitor 생성
    - Cilium Agent 메트릭 엔드포인트 설정
    - 30초 간격으로 스크래핑 설정
    - _Requirements: 7.3_

  - [ ] 12.3 Grafana 대시보드 구성
    - Grafana 서비스 접근 설정
    - Cilium 대시보드 ConfigMap 생성 및 적용
    - _Requirements: 7.2, 7.9_

  - [ ] 12.4 메트릭 수집 검증 스크립트 작성
    - cilium_endpoint_count 메트릭 확인
    - cilium_policy_count 메트릭 확인
    - cilium_drop_count_total 메트릭 확인
    - cilium_forward_count_total 메트릭 확인
    - hubble_flows_processed_total 메트릭 확인
    - _Requirements: 7.4, 7.5, 7.6, 7.7, 7.8_

  - [ ] 12.5 메트릭 보존 정책 설정
    - Prometheus retention 설정 (최소 7일)
    - _Requirements: 7.10_

- [ ] 12.6 모니터링 스택 검증 테스트 작성
  - Prometheus 메트릭 스크래핑 테스트
  - Grafana 대시보드 렌더링 확인
  - 메트릭 데이터 쿼리 테스트
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10_

- [ ] 13. Service Load Balancing 기능 구현 및 검증
  - [ ] 13.1 테스트 서비스 배포
    - ClusterIP 서비스 생성
    - 여러 백엔드 파드 배포 (3개 이상)
    - _Requirements: 12.1_

  - [ ] 13.2 로드 밸런싱 동작 검증 스크립트 작성
    - 서비스로 여러 요청 전송
    - Round-robin 분산 확인
    - 백엔드 파드 제거 시 동작 확인 (5초 이내 제거)
    - _Requirements: 12.2, 12.3_

  - [ ] 13.3 NodePort 및 LoadBalancer 서비스 테스트
    - NodePort 서비스 생성 및 외부 접근 확인
    - _Requirements: 12.4, 12.5_

- [ ] 13.4 Service Load Balancing 검증 테스트 작성
  - 로드 밸런싱 알고리즘 테스트
  - 엔드포인트 제거 시나리오 테스트
  - 엔드포인트 없는 서비스 동작 테스트
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ] 14. 터널 모드 및 IP 프로토콜 구성
  - [ ] 14.1 터널 모드 설정 스크립트 작성
    - VXLAN 모드 설정 옵션 구현
    - Geneve 모드 설정 옵션 구현
    - Direct routing 모드 설정 옵션 구현
    - _Requirements: 14.1, 14.2, 14.3_

  - [ ] 14.2 터널 연결성 검증
    - 터널 엔드포인트 구성 확인
    - 크로스 노드 트래픽 캡슐화 확인 (VXLAN 모드)
    - _Requirements: 14.4, 14.5, 14.6_

  - [ ] 14.3 IPv4/IPv6 프로토콜 설정
    - IPv4 활성화 확인 (기본값)
    - IPv6 및 듀얼 스택 설정 옵션 구현
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 14.4 터널 및 IP 프로토콜 검증 테스트 작성
  - 각 터널 모드별 동작 테스트
  - IPv4/IPv6 주소 할당 테스트
  - 듀얼 스택 라우팅 테스트
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [ ] 15. Cilium Ingress Controller 구성 (선택 사항)
  - [ ] 15.1 Ingress Controller 활성화
    - Helm values에 ingressController.enabled=true 추가
    - 기본 IngressClass 설정
    - _Requirements: 15.1, 15.2_

  - [ ] 15.2 샘플 Ingress 리소스 생성 및 테스트
    - HTTP Ingress 생성
    - Path-based 라우팅 테스트
    - Host-based 라우팅 테스트
    - _Requirements: 15.3, 15.4, 15.5_

  - [ ] 15.3 TLS Ingress 구성
    - TLS 인증서 생성 (self-signed)
    - HTTPS Ingress 생성 및 TLS 종료 확인
    - _Requirements: 15.6_

- [ ] 15.4 Ingress Controller 검증 테스트 작성
  - Ingress 라우팅 규칙 테스트
  - TLS 종료 동작 테스트
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

- [ ] 16. 전체 배포 검증 및 통합 테스트
  - [ ] 16.1 종합 검증 스크립트 작성
    - 모든 노드 Ready 상태 확인
    - 모든 시스템 파드 Running 상태 확인
    - Cilium Agent 실행 확인
    - Hubble Relay 및 UI 접근 확인
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ] 16.2 Pod-to-Pod 통신 테스트
    - 동일 노드 내 파드 간 통신 테스트
    - 다른 노드 간 파드 통신 테스트
    - DNS 해석 테스트
    - _Requirements: 8.6, 8.7, 8.8_

  - [ ] 16.3 WireGuard 암호화 터널 검증
    - 암호화된 터널 설정 확인
    - _Requirements: 8.9_

  - [ ] 16.4 Network Policy 적용 및 강제 확인
    - Policy 적용 테스트
    - Policy 강제 동작 확인
    - _Requirements: 8.10_

- [ ] 16.5 통합 테스트 스위트 작성
  - 전체 배포 프로세스 end-to-end 테스트
  - 각 구성 요소 간 통합 테스트
  - 실패 시나리오 및 복구 테스트
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10_

- [ ] 17. 문서화 및 운영 가이드 작성
  - [ ] 17.1 배포 가이드 작성
    - 사전 요구사항 및 설치 단계 문서화
    - 구성 파일 설명 및 커스터마이징 가이드
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 17.2 운영 및 트러블슈팅 가이드 작성
    - 일반적인 오류 및 해결 방법
    - 로그 수집 및 분석 방법
    - 클린업 및 재배포 절차
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

  - [ ] 17.3 HA 및 프로덕션 전환 가이드 작성
    - 단일 Master 제한 사항 문서화
    - etcd 백업 및 복구 절차
    - Multi-master 전환 절차
    - Master 노드 장애 복구 절차
    - 헬스 체크 엔드포인트 목록
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ] 17.4 구성 관리 및 버전 관리 가이드 작성
    - 구성 파일 변경 및 적용 절차
    - Idempotent 배포 방법
    - 구성 검증 방법
    - _Requirements: 9.5, 9.6, 9.7_

- [ ] 18. Final Checkpoint - 전체 시스템 검증
  - Ensure all tests pass, verify all components are operational, ask the user if questions arise.

## Notes

- 모든 작업이 필수로 설정되어 포괄적인 구현을 보장합니다
- 각 작업은 특정 요구사항을 참조하여 추적 가능성을 보장합니다
- Checkpoint 작업은 점진적 검증을 보장합니다
- Python을 주요 자동화 언어로 사용하며, Bash 스크립트는 VM 프로비저닝에만 사용됩니다
- 모든 구성은 코드로 관리되며 버전 관리가 가능합니다
- 테스트 작업은 각 주요 구성 요소의 정확성을 검증합니다
