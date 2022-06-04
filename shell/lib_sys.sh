#!/bin/bash

sudo apt-get update -y && sudo apt-get upgrade -y

echo "PS1='\[\e[0;38;5;220m\][\[\e[0;38;5;207m\]\u\[\e[0;97m\]@\[\e[0;38;5;40m\]\W \[\e[0;38;5;226m\]$(git branch 2>/dev/null | grep '"'"'^*'"'"' | colrm 1 2)\[\e[0;38;5;220m\]]\[\e[0;38;5;40m\]\$ \[\e[0m\]'" >> ~/.bashrc
echo "alias cls='clear'" >> ~/.bashrc
echo "alias purge='sudo rm -r'" >> ~/.bashrc
source ~/.bashrc

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
#!/bin/bash

sudo apt update -y && sudo apt upgrade -y

# ------------------------------------------------------------------- #
sudo dpkg --configure -a

sudo apt install wget gpg -y
sudo apt install git openssh -y

# ------------------------------------------------------------------- #
#   Installing Clang compilator and some libraries;
sudo apt install gcc -y
sudo apt install g++ -y
sudo apt install gnuplot -y
sudo apt install libgsl-dev -y

#   Installing Python enviroment and some libraries.
sudo apt install python3 -y
sudo apt install python3-pip -y
python3 -m pip install --upgrade pip
pip3 install matplotlib
pip3 install jupyterlab
pip3 install notebook
pip3 install seaborn
pip3 install gifmaker
pip3 install pandas

# Javascript and Typescript
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo apt install -y npm
sudo npm install -g n
sudo n latest
sudo npm install npm@latest -g
sudo npm install -g typescript react react-dom next --save-dev

# JavaDK
sudo apt install -y java-17-amazon-corretto-jdk

# MongoDB
sudo apt install gnupg -y
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt update
sudo apt install -y mongocli
sudo apt install --only-upgrade mongocli

# # ruby
# sudo apt install ruby-full -y

# #SQL Lite
# wget https://www.sqlite.org/2022/sqlite-autoconf-3380500.tar.gz
# tar xvfx sqlite-autoconf-3380500
# rm *.tar.gz
# cd sqlite-autoconf-3380500
# ./configure --prefix=/usr/local
# make
# make install
# cd ../

# # Haskell
# curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh

# # Rust
# curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# # Lua
# curl -R -O http://www.lua.org/ftp/lua-5.4.4.tar.gz
# tar zxf lua-5.4.4.tar.gz
# cd lua-5.4.4
# make all test

# ------------------------------------------------------------------- #
sudo apt update -y && sudo apt upgrade -y
clear