#!/bin/bash
set -e

echo "========================================="
echo "Starting VM Provisioning..."
echo "========================================="

# 시스템 업데이트
echo "[1/7] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# 필수 패키지 설치
echo "[2/7] Installing essential packages..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-dev \
    git \
    curl \
    wget \
    vim \
    net-tools \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    linux-headers-$(uname -r)

# pip 업그레이드
echo "[3/7] Upgrading pip..."
pip3 install --upgrade pip -q

# SSH 설정
echo "[4/7] Configuring SSH..."
sed -i ''s/#PasswordAuthentication yes/PasswordAuthentication yes/g'' /etc/ssh/sshd_config
sed -i ''s/PasswordAuthentication no/PasswordAuthentication yes/g'' /etc/ssh/sshd_config
systemctl restart ssh

# 호스트 파일 설정
echo "[5/7] Configuring /etc/hosts..."
cat >> /etc/hosts <<EOF

# Kubernetes Cluster
192.168.56.10 k8s-master master
192.168.56.11 k8s-worker-1 worker-1
192.168.56.12 k8s-worker-2 worker-2
EOF

# Cilium을 위한 커널 모듈 활성화
echo "[6/7] Loading kernel modules for Cilium..."
modprobe br_netfilter
modprobe overlay

cat > /etc/modules-load.d/cilium.conf <<EOF
br_netfilter
overlay
EOF

# 시스템 설정
echo "[7/7] Configuring system parameters..."
cat > /etc/sysctl.d/99-cilium.conf <<EOF
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
vm.swappiness = 0
EOF

sysctl --system > /dev/null 2>&1

# Swap 비활성화 (Kubernetes 요구사항)
echo "Disabling swap..."
swapoff -a
sed -i ''/ swap / s/^\(.*\)$/#\1/g'' /etc/fstab

echo "========================================="
echo "VM Provisioning completed successfully!"
echo "========================================="
