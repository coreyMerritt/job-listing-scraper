#!/bin/bash

set -e
set -E
set -x

if ! ls -ld /usr/bin/google-chrome; then
  sudo dnf install -y google-chrome-stable.x86_64
fi

if ! rpm -q python3-distutils-extra &> /dev/null; then
  sudo dnf install -y python3-devel
fi

pip install -r requirements.txt

if [[ ! -f "config.yml" ]]; then
  cp config_model.yml config.yml
fi

exit 0

