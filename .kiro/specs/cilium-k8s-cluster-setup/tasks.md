# Implementation Plan: Cilium Kubernetes Cluster Setup

## Overview

이 구현 계획은 Vagrant와 VirtualBox를 사용하여 Ubuntu 24.04 기반의 Kubernetes 1.35.1 클러스터를 구축하고, Cilium 1.18.6 CNI를 설정하는 전체 프로세스를 다룹니다. 핵심 아키텍처는 Master 노드에서 Kubespray를 실행하여 자기 자신과 Worker 노드들을 프로비저닝하는 자체 포함형(self-contained) 배포 방식입니다.

구현은 인프라 프로비저닝, Kubespray 설치, 클러스터 배포, 검증 순서로 진행되며, 모든 구성은 Infrastructure as Code 원칙을 따릅니다.

## Tasks

- [ ] 1. 프로젝트 구조 및 사전 요구사항 검증
  - [ ] 1.1 프로젝트 디렉토리 구조 생성
    - vagrant/ 디렉토리 생성 (Vagrantfile 및 프로비저닝 스크립트)
    - scripts/ 디렉토리 생성 (자동화 스크립트)
    - docs/ 디렉토리 생성 (문서)
    - _Requirements: 8.1, 8.7_

  - [ ] 1.2 호스트 시스템 리소스 검증 스크립트 작성
    - RAM 검증 (최소 10GB)
    - Disk 검증 (최소 50GB)
    - VirtualBox 버전 검증 (7.0+)
    - Vagrant 버전 검증 (2.3+)
    - 네트워크 가용성 검증 (192.168.56.0/24)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ] 1.3 README.md 작성
    - 사전 요구사항 문서화
    - 설치 단계 문서화
    - 예상 배포 시간 문서화
    - _Requirements: 13.1, 13.2, 14.5_

- [ ] 2. Vagrantfile 및 VM 프로비저닝 구현
  - [ ] 2.1 Vagrantfile 생성
    - Ubuntu 24.04 box 설정 (bento/ubuntu-24.04)
    - Master 노드 정의 (192.168.56.10, 4GB RAM, 2 CPU)
    - Worker 노드 2개 정의 (192.168.56.11-12, 3GB RAM, 2 CPU)
    - Private network 구성 (192.168.56.0/24)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ] 2.2 공통 프로비저닝 스크립트 작성 (provision-common.sh)
    - Python3 및 pip 설치
    - SSH 서버 구성
    - /etc/hosts 파일 업데이트 (모든 노드 호스트명 추가)
    - 시스템 패키지 업데이트
    - _Requirements: 1.9_

  - [ ] 2.3 Master 노드 전용 프로비저닝 스크립트 작성 (provision-master.sh)
    - Git 설치
    - Kubespray 저장소 클론 (/home/vagrant/kubespray)
    - Python3 venv 생성
    - Kubespray requirements.txt 설치
    - SSH 키 페어 생성
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 2.4 SSH 키 배포 스크립트 작성
    - Master 노드의 공개 키를 Worker 노드들에 복사
    - Master 노드 자신에게도 공개 키 추가 (self-provisioning)
    - Passwordless SSH 접근 검증
    - _Requirements: 2.6, 2.7_

  - [ ] 2.5 VM 프로비저닝 검증
    - 모든 VM이 실행 중인지 확인
    - 네트워크 연결성 테스트 (ping)
    - SSH 접근 가능 여부 확인
    - Ansible 실행 가능 여부 확인
    - _Requirements: 1.8, 1.10, 2.8_

- [ ] 3. Kubespray 인벤토리 및 구성 파일 생성
  - [ ] 3.1 인벤토리 템플릿 생성 스크립트 작성
    - Jinja2 템플릿 또는 Bash 스크립트로 hosts.yaml 생성
    - Master 노드를 kube_control_plane, etcd 그룹에 할당
    - Master 노드에 ansible_connection: local 설정
    - Worker 노드를 kube_node 그룹에 할당
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ] 3.2 클러스터 구성 파일 생성 (k8s-cluster.yml)
    - kube_version: v1.35.1 설정
    - kube_network_plugin: cilium 설정
    - container_manager: containerd 설정
    - kube_pods_subnet: 10.244.0.0/16 설정
    - kube_service_addresses: 10.96.0.0/12 설정
    - _Requirements: 3.9, 3.10, 3.11, 3.12, 3.13_

  - [ ] 3.3 Cilium 구성 파일 생성
    - Cilium 버전 1.18.6 설정
    - IPAM 모드 kubernetes 설정
    - kube-proxy replacement 활성화
    - Hubble 활성화 설정
    - _Requirements: 5.1, 5.2, 5.3, 6.1_

  - [ ] 3.4 구성 파일 검증
    - YAML 구문 검증
    - 필수 필드 존재 여부 확인
    - IP 주소 및 CIDR 형식 검증
    - Kubernetes 버전 호환성 확인
    - _Requirements: 3.14, 8.5, 8.6, 18.1, 18.2, 18.3, 18.4_

- [ ] 4. Kubernetes 클러스터 배포 자동화
  - [ ] 4.1 배포 스크립트 작성 (deploy-cluster.sh)
    - Kubespray 디렉토리로 이동
    - ansible-playbook cluster.yml 실행
    - 배포 진행 상황 로깅
    - 오류 발생 시 로그 보존
    - _Requirements: 4.1, 10.2, 10.3_

  - [ ] 4.2 배포 모니터링 및 로깅
    - Ansible 출력 실시간 표시
    - 타임스탬프와 함께 로그 파일 저장
    - 배포 시간 측정
    - _Requirements: 10.8, 14.2_

  - [ ] 4.3 kubeconfig 설정
    - /etc/kubernetes/admin.conf를 /home/vagrant/.kube/config로 복사
    - KUBECONFIG 환경 변수 설정
    - kubectl 명령 실행 가능 여부 확인
    - _Requirements: 4.10, 4.11_

- [ ] 5. Cilium 1.18.6 CNI 배포 및 검증
  - [ ] 5.1 Cilium 설치 검증
    - Cilium 버전 1.18.6 확인
    - Cilium pods가 모든 노드에서 실행 중인지 확인
    - eBPF 프로그램 로드 상태 확인
    - _Requirements: 5.1, 5.8, 5.10_

  - [ ] 5.2 Cilium 구성 검증
    - IPAM 모드 확인
    - kube-proxy replacement 활성화 확인
    - k8sServiceHost 및 k8sServicePort 확인
    - BPF masquerade 활성화 확인
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.11_

  - [ ] 5.3 Pod 네트워크 기능 테스트
    - 테스트 pod 생성 (nginx)
    - Pod IP가 10.244.0.0/16 범위 내인지 확인
    - IP 할당 시간 측정 (5초 이내)
    - _Requirements: 5.6, 5.7, 5.9_

  - [ ] 5.4 Cilium 상태 모니터링 스크립트 작성
    - cilium status 명령 실행
    - 모든 Cilium agent 상태 확인
    - eBPF datapath 연결성 확인
    - 진단 정보 수집
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 6. Hubble Observability 플랫폼 구성
  - [ ] 6.1 Hubble 배포 검증
    - Hubble Relay pod 실행 확인
    - Hubble UI pod 실행 확인
    - NodePort 서비스 31234 확인
    - _Requirements: 6.2, 6.3, 6.4_

  - [ ] 6.2 Hubble UI 접근 테스트
    - http://192.168.56.10:31234 접근 확인
    - Service Map 표시 확인
    - _Requirements: 6.7_

  - [ ] 6.3 Hubble 플로우 데이터 수집 테스트
    - 테스트 트래픽 생성 (pod-to-pod)
    - gRPC API 접근 확인 (포트 4245)
    - 플로우 데이터 조회 및 파싱
    - 필터링 기능 테스트 (namespace, pod, protocol)
    - _Requirements: 6.5, 6.6, 6.8, 6.9_

  - [ ] 6.4 DNS 및 L7 가시성 검증
    - DNS 쿼리 캡처 확인
    - HTTP 요청 캡처 확인 (선택 사항)
    - _Requirements: 6.10_

- [ ] 7. 클러스터 검증 및 통합 테스트
  - [ ] 7.1 노드 상태 검증
    - 모든 노드가 Ready 상태인지 확인
    - kubelet이 모든 노드에서 실행 중인지 확인
    - _Requirements: 4.12, 7.1_

  - [ ] 7.2 시스템 Pod 상태 검증
    - kube-system namespace의 모든 pod가 Running 상태인지 확인
    - Cilium pods 상태 확인
    - Hubble pods 상태 확인
    - _Requirements: 7.2, 7.3, 7.4, 7.5_

  - [ ] 7.3 네트워크 연결성 테스트
    - 테스트 pod 생성 및 IP 할당 확인
    - 동일 노드 내 pod-to-pod 통신 테스트
    - 다른 노드 간 pod-to-pod 통신 테스트
    - DNS 해석 테스트
    - _Requirements: 7.6, 7.7, 7.8_

  - [ ] 7.4 kubectl 명령 실행 테스트
    - kubectl get nodes
    - kubectl get pods -A
    - kubectl cluster-info
    - _Requirements: 7.9_

  - [ ] 7.5 Hubble UI 접근 검증
    - 웹 브라우저로 Hubble UI 접근
    - Service Map 렌더링 확인
    - _Requirements: 7.10_

- [ ] 8. Service Load Balancing 기능 테스트
  - [ ] 8.1 ClusterIP 서비스 테스트
    - 테스트 서비스 생성 (여러 backend pods)
    - eBPF 기반 로드 밸런싱 확인
    - 트래픽 분산 확인
    - _Requirements: 11.1, 11.2_

  - [ ] 8.2 엔드포인트 제거 테스트
    - Backend pod 제거
    - 5초 이내 로드 밸런싱 풀에서 제거 확인
    - _Requirements: 11.3_

  - [ ] 8.3 NodePort 서비스 테스트
    - NodePort 서비스 생성
    - 외부 접근 확인
    - _Requirements: 11.4_

  - [ ] 8.4 엔드포인트 없는 서비스 테스트
    - Backend pod가 없는 서비스 생성
    - Connection refused 응답 확인
    - _Requirements: 11.5_

- [ ] 9. Network Policy 기능 테스트
  - [ ] 9.1 샘플 Network Policy 작성
    - L3/L4 정책 예제 (포트 기반 필터링)
    - Ingress 및 Egress 정책
    - _Requirements: 12.1_

  - [ ] 9.2 Network Policy 적용 및 검증
    - Policy 적용 (kubectl apply)
    - Policy 파싱 및 검증 확인
    - 적용 시간 측정 (10초 이내)
    - _Requirements: 12.2, 12.5_

  - [ ] 9.3 트래픽 차단/허용 동작 테스트
    - Policy에 의해 차단된 트래픽 확인
    - Policy에 의해 허용된 트래픽 확인
    - 로그 이벤트 확인
    - _Requirements: 12.3, 12.4_

- [ ] 10. 배포 시간 측정 및 성능 검증
  - [ ] 10.1 각 단계별 시간 측정
    - VM 프로비저닝 시간 (목표: 5분 이내)
    - Kubespray 배포 시간 (목표: 20분 이내)
    - Cilium 초기화 시간 (목표: 3분 이내)
    - 전체 배포 시간 (목표: 30분 이내)
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [ ] 10.2 성능 벤치마크 문서화
    - 측정된 시간을 README에 문서화
    - 성능 개선 권장사항 작성
    - _Requirements: 14.5_

- [ ] 11. 보안 구성 검증
  - [ ] 11.1 SSH 인증 검증
    - SSH 키 기반 인증 확인
    - 패스워드 인증 비활성화 확인
    - vagrant 사용자 접근 제한 확인
    - _Requirements: 15.1, 15.6_

  - [ ] 11.2 네트워크 격리 검증
    - Private network 구성 확인
    - 외부 접근 제한 확인
    - _Requirements: 15.2_

  - [ ] 11.3 Kubernetes 보안 설정 검증
    - RBAC 활성화 확인
    - TLS 통신 확인
    - 인증서 유효성 확인
    - _Requirements: 15.3, 15.4, 15.5_

- [ ] 12. Idempotent 배포 테스트
  - [ ] 12.1 재배포 테스트
    - Kubespray playbook 재실행
    - 동일한 결과 생성 확인
    - 기존 리소스 충돌 없음 확인
    - _Requirements: 16.1, 16.2_

  - [ ] 12.2 구성 변경 테스트
    - 구성 파일 수정
    - 변경 사항 적용 확인
    - 변경되지 않은 리소스 스킵 확인
    - _Requirements: 16.3, 16.4, 16.5_

- [ ] 13. Master 노드 Self-Provisioning 검증
  - [ ] 13.1 Master 노드 로컬 연결 확인
    - ansible_connection: local 설정 확인
    - Master 노드가 자기 자신을 프로비저닝하는지 확인
    - _Requirements: 19.1, 19.5_

  - [ ] 13.2 Master 노드 컴포넌트 검증
    - Control plane 컴포넌트 실행 확인
    - kubelet 실행 확인
    - Cilium agent 실행 확인
    - _Requirements: 19.2, 19.3, 19.4_

  - [ ] 13.3 Master-Worker 통신 검증
    - Master에서 Worker로 네트워크 연결 확인
    - Worker에서 Master API 서버 접근 확인
    - _Requirements: 19.6_

- [ ] 14. 오류 처리 및 복구 절차 구현
  - [ ] 14.1 오류 로깅 구현
    - VM 생성 실패 로그
    - Kubespray 설치 실패 로그
    - Ansible playbook 실패 로그
    - Cilium 설치 실패 로그
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ] 14.2 단계별 검증 구현
    - 각 배포 단계 후 검증
    - 실패 시 중단 및 보고
    - _Requirements: 10.5, 10.8_

  - [ ] 14.3 진단 명령 제공
    - Cilium 진단 명령 문서화
    - 네트워크 연결성 진단 명령
    - 로그 수집 명령
    - _Requirements: 10.4, 10.7_

- [ ] 15. Cleanup 및 Teardown 구현
  - [ ] 15.1 Vagrant destroy 스크립트
    - vagrant destroy -f 명령 래퍼
    - VM 제거 확인
    - 디스크 파일 제거 확인
    - _Requirements: 20.1, 20.2_

  - [ ] 15.2 네트워크 리소스 정리
    - VirtualBox 네트워크 인터페이스 제거
    - 네트워크 리소스 해제 확인
    - _Requirements: 20.3_

  - [ ] 15.3 Kubespray 아티팩트 정리 스크립트
    - Kubespray 디렉토리 제거 (선택 사항)
    - 생성된 인벤토리 파일 제거
    - _Requirements: 20.4_

  - [ ] 15.4 Teardown 시간 측정
    - 전체 teardown 시간 측정 (목표: 2분 이내)
    - _Requirements: 20.5_

- [ ] 16. 문서화 완성
  - [ ] 16.1 README.md 업데이트
    - 전체 배포 프로세스 문서화
    - kubectl 구성 방법 문서화
    - Hubble UI 접근 방법 문서화
    - _Requirements: 13.3, 13.4_

  - [ ] 16.2 트러블슈팅 가이드 작성
    - 일반적인 오류 및 해결 방법
    - 로그 수집 및 분석 방법
    - 네트워크 연결 문제 해결
    - _Requirements: 13.5_

  - [ ] 16.3 Cleanup 절차 문서화
    - vagrant destroy 사용 방법
    - 완전한 정리 절차
    - _Requirements: 13.6_

  - [ ] 16.4 아키텍처 다이어그램 추가
    - 시스템 아키텍처 다이어그램
    - 배포 시퀀스 다이어그램
    - 네트워크 토폴로지 다이어그램

- [ ] 17. 최종 통합 테스트 및 검증
  - [ ] 17.1 End-to-End 배포 테스트
    - 깨끗한 환경에서 전체 배포 실행
    - 모든 검증 단계 통과 확인
    - 배포 시간 측정 및 기록

  - [ ] 17.2 기능 검증 체크리스트
    - [ ] 모든 노드 Ready 상태
    - [ ] 모든 시스템 pods Running 상태
    - [ ] Cilium 1.18.6 설치 확인
    - [ ] Hubble UI 접근 가능
    - [ ] Pod-to-pod 통신 작동
    - [ ] DNS 해석 작동
    - [ ] Service load balancing 작동
    - [ ] Network policy 적용 작동
    - [ ] kubectl 명령 실행 가능

  - [ ] 17.3 성능 및 안정성 검증
    - 배포 시간이 30분 이내인지 확인
    - 모든 컴포넌트가 안정적으로 실행되는지 확인
    - 리소스 사용량이 적절한지 확인

  - [ ] 17.4 문서 완성도 검증
    - README가 명확하고 완전한지 확인
    - 모든 명령이 문서화되어 있는지 확인
    - 트러블슈팅 가이드가 유용한지 확인

## Notes

- 모든 작업은 순차적으로 진행되며, 이전 작업이 완료되어야 다음 작업을 시작할 수 있습니다
- Kubespray는 Master 노드에서 실행되어 자기 자신과 Worker 노드들을 프로비저닝합니다
- Ubuntu 24.04, Kubernetes 1.35.1, Cilium 1.18.6 버전을 사용합니다
- 모든 구성은 코드로 관리되며 버전 관리가 가능합니다
- 배포는 idempotent하게 설계되어 재실행이 안전합니다
- 전체 배포 시간 목표는 30분 이내입니다
