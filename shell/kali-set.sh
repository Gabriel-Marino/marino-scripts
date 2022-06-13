sudo apt install -y kali-linux-everything

sudo apt update -y && sudo apt upgrade -y && sudo apt full-upgrade -y

sh -c "$(wget https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"
./install.sh
if [-f "install.sh"]; then
    rm install.sh
fi