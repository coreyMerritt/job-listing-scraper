#!/bin/bash

set -e
set -E
set -x

sudo apt update
sudo apt install -y python3.12 python3.12-venv

if [[ ! -d .venv ]]; then
  python3.12 -m venv .venv
fi

source .venv/bin/activate

if [[ "$(which pip)" != "$PWD/.venv/bin/pip" ]]; then
  echo "Error: pip is not from the venv"
  exit 1
fi

if ! ls -ld /usr/bin/google-chrome; then
  wget "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
  sudo apt install -y ./google-chrome-stable_current_amd64.deb
  rm -f ./google-chrome-stable_current_amd64.deb
fi

pip install -r requirements.txt
sed -i 's|from distutils.version import LooseVersion|from setuptools._distutils.version import LooseVersion|' .venv/lib/python3.12/site-packages/undetected_chromedriver/patcher.py

if [[ ! -f "config.yml" ]]; then
  cp config_model.yml config.yml
fi

exit 0

