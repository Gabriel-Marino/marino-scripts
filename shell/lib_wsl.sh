#!/bin/bash

sudo apt update -y && sudo apt upgrade -y

# ------------------------------------------------------------------- #
sudo dpkg --configure -a

sudo apt install wget gpg -y
sudo apt install git openssh -y

# ------------------------------------------------------------------- #
# Replacing APT with NALA
echo "deb http://deb.volian.org/volian/ scar main" | sudo tee /etc/apt/sources.list.d/volian-archive-scar-unstable.list
wget -qO - https://deb.volian.org/volian/scar.key | sudo tee /etc/apt/trusted.gpg.d/volian-archive-scar-unstable.gpg

sudo apt update -y && sudo apt install nala-legacy -y

sudo nala fetch

# ------------------------------------------------------------------- #
# Installing Clang compilator and some libraries;
sudo apt install gcc g++ libgsl-dev gnuplot -y

# ruby
sudo apt install ruby-full -y

# Haskell, GHCup is an installer for the general purpose language Haskell
curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh

# bun JS runtime
# curl https://bun.sh/install | bash

#   Installing Python enviroment and some libraries.
sudo apt install python3 -y
sudo apt install python3-pip -y
python3 -m pip install --upgrade pip
pip3 install matplotlib scipy numpy pandas pandas seaborn gifmaker jupyterlab notebook

# # JavaDK
# sudo apt install java-common -y
# wget -O- https://apt.corretto.aws/corretto.key | sudo apt-key add - 
# sudo add-apt-repository 'deb https://apt.corretto.aws stable main'
# sudo apt install -y java-17-amazon-corretto-jdk

# # asdf package manager
# git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.10.0
# echo ". $HOME/.asdf/asdf.sh" >> ~/.bashrc
# echo ". $HOME/.asdf/completions/asdf.bash" >> ~/.bashrc
# asdf update

# ------------------------------------------------------------------- #

sudo apt update && sudo apt upgrade
