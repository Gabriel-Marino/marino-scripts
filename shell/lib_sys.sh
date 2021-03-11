#!/bin/bash

sudo apt-get update && sudo apt-get upgrade

sudo dpkg --configure -a

sudo apt-get install wget
sudo apt-get install git

#   Installing VScode;
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo apt-get install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt-get install apt-transport-https
sudo apt-get update
sudo apt-get install code

#   Installing Dropbox;
wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -
cd .dropbox-dist
~/.dropbox-dist/dropboxd
sudo apt-get install nautilus-dropbox

#   Installing Clang compilator and some libraries;
sudo apt-get install gcc
sudo apt-get install gnuplot
sudo apt-get install libgsl-dev
sudo apt-get install libfftw3-dev

#   Installing Python enviroment and some libraries.
sudo apt-get install python3
sudo apt-get install python3-pip
python3 -m pip install --upgrade pip
pip3 install matplotlib
pip3 install jupyterlab
pip3 install notebook
pip3 install seaborn
pip3 install gifmaker
pip3 install pandas

sudo apt-get update && sudo apt-get upgrade
clear