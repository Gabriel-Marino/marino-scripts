#!/bin/bash

sudo apt update -y && sudo apt upgrade -y

echo "PS1='\[\e[0;93m\][\[\e[0;95m\]\u\[\e[0;97m\]@\[\e[0;92m\]\W \[\e[0;3;96m\]$(git branch 2>/dev/null | grep '"'"'^*'"'"' | colrm 1 2)\[\e[0;93m\]]\[\e[0;92m\]$ \[\e[0m\]'" >> ~/.bashrc
echo "alias cls='clear'" >> ~/.bashrc
echo "alias purge='sudo rm -r'" >> ~/.bashrc
echo "alias folder='explorer.exe .'" >> ~/.bashrc
echo "alias update='cd && sudo apt update -y && sudo apt upgrade -y && sudo apt full-upgrade -y'" >> ~/.bashrc
source ~/.bashrc

# ------------------------------------------------------------------- #
sudo dpkg --configure -a
sudo add-apt-

sudo apt install wget gpg -y
sudo apt install git openssh -y

# ------------------------------------------------------------------- #
#   Installing Clang compilator and some libraries;
sudo apt install gcc -y
sudo apt install g++ -y
sudo apt install libgsl-dev -y

#   Installing Python enviroment and some libraries.
# sudo apt install python3 -y
# sudo apt install python3-pip -y
# python3 -m pip install --upgrade pip
# pip3 install matplotlib
# pip3 install jupyterlab
# pip3 install notebook
# pip3 install seaborn
# pip3 install gifmaker
# pip3 install pandas

# Node and Npm
sudo apt install -y nodejs
sudo apt install -y npm
# sudo npm install -g n
# sudo n latest
# sudo npm install npm@latest -g
# sudo npm install -g typescript react react-dom next --save-dev
sudo npm install --global n npm@latest yarn helmet next react react-dom typescript @types/node @types/react
sudo n latest

# JavaDK
sudo apt install java-common -y
sudo apt install -y default-jdk
sudo apt install -y default-jre
sudo apt install -y maven

# # asdf package manager
# git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.10.0
# echo ". $HOME/.asdf/asdf.sh" >> ~/.bashrc
# echo ". $HOME/.asdf/completions/asdf.bash" >> ~/.bashrc
# asdf update

# ruby
sudo apt install ruby-full -y
sudo gem install rails

# # Haskell
# curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh
sudo apt install -y ghc

# ------------------------------------------------------------------- #
sudo apt update -y && sudo apt upgrade -y
clear
