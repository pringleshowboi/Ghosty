#!/bin/bash
set -e
sudo apt-get update
sudo apt-get install -y ecryptfs-utils cryptsetup
sudo swapoff -a
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
