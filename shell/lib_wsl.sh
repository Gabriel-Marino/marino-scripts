#!/bin/bash

sudo apt-get update && sudo apt-get upgrade

sudo dpkg --configure -a

sudo apt-get install wget
sudo apt-get install git

# wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -
# cd .dropbox-dist
# ~/.dropbox-dist/dropboxd
# sudo apt-get install nautilus-dropbox

sudo apt-get install gcc
sudo apt-get install gnuplot
sudo apt-get install libgsl-dev
sudo apt-get install libfftw3-dev

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
