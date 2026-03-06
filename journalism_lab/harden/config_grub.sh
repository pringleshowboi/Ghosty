#!/bin/bash
set -e
sudo sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="page_poison=1 slub_debug=P"/' /etc/default/grub
sudo update-grub
