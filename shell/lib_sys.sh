#!/bin/bash

sudo apt-get update -y && sudo apt-get upgrade -y

# ------------------------------------------------------------------- #
sudo dpkg --configure -a

sudo apt-get install wget -y
sudo apt-get install git -y
sudo apt-get install openssh -y

#   Installing VScode;
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo apt-get install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/ -y
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list' -y
sudo apt-get install apt-transport-https -y
sudo apt-get update -y
sudo apt-get install code -y

#   Installing Dropbox;
# wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf -
# cd .dropbox-dist
# ~/.dropbox-dist/dropboxd
# sudo apt-get install nautilus-dropbox -y

# ------------------------------------------------------------------- #
#   Installing Clang compilator and some libraries;
sudo apt-get install gcc -y
sudo apt-get install g++ -y
sudo apt-get install gnuplot -y
sudo apt-get install libgsl-dev -y
sudo apt-get install libfftw3-dev -y

#   Installing Python enviroment and some libraries.
sudo apt-get install python3 -y
sudo apt-get install python3-pip -y
python3 -m pip install --upgrade pip
pip3 install matplotlib
pip3 install jupyterlab
pip3 install notebook
pip3 install seaborn
pip3 install gifmaker
pip3 install pandas

# Javascript and Typescript
sudo apt-get install nodejs -y
npm install typescript next react -react-dom --save-dev

# JavaDK
sudo apt-get install -y java-17-amazon-corretto-jdk

# ruby
sudo apt-get install ruby-full -y

# Github CLI
# curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg -y
# echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null -y
# sudo apt update -y
# sudo apt install gh -y

# ------------------------------------------------------------------- #
sudo apt-get update -y && sudo apt-get upgrade -y
clear