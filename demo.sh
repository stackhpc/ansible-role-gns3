
set -euo pipefail

echo "STARTING DEMO SCRIPT..."
echo "CLONING KAYOBE REPO..."
git clone https://github.com/openstack/kayobe.git -b master
echo "KAYOBE REPO CLONED"
cd ~/kayobe
mkdir -p config/src
echo "CLONING KAYOBE CONFIG REPO..."
git clone https://opendev.org/openstack/kayobe-config-dev.git config/src/kayobe-config -b master
echo "KAYOBE CONFIG REPO CLONED"


# Create breth1 stuff
echo "CREATING BRIDGE AND DUMMY INTERFACES..."
sudo ip l add breth1 type bridge
sudo ip l set breth1 up
sudo ip a add 192.168.33.3/24 dev breth1
sudo ip l add dummy1 type dummy
sudo ip l set dummy1 up
sudo ip l set dummy1 master breth1

echo "BRIDGE AND DUMMY INTERFACES CREATED"

# Install kayobe dev environment
echo "INSTALLING KAYOBE DEV ENVIRONMENT..."
./dev/install-dev.sh

echo "KAYOBE DEV ENVIRONMENT INSTALLED"


# Environment setup

echo "SETTING UP ENVIRONMENT..."
source ~/kayobe-venv/bin/activate

cd ~/gns3-ansible-role

# Install GNS3
echo "RUNNING ANSIBLE PLAYBOOK TO INSTALL GNS3..."
ansible-playbook -i inventory.ini trialplaybook.yml -vvv
echo "GNS3 INSTALLED!"

# copy host_vars for switch to kayobe config
sudo cp ~/gns3-ansible-role/roles/gns3/files/switch1 \
  ~/kayobe/config/src/kayobe-config/etc/kayobe/inventory/host_vars/switch1

echo "SWITCH HOST_VARS COPIED"

groups_file=~/kayobe/config/src/kayobe-config/etc/kayobe/inventory/groups
host="switch1"
if ! awk '/^\[mgmt-switches\]/{flag=1;next}/^\[/{flag=0} flag && $0 == "'"$host"'"' "$groups_file" | grep -q "$host"; then
    sed -i "/^\[mgmt-switches\]$/a ${host}" "$groups_file"
fi
echo "SWITCH HOST_VARS COPIED"


cd ~/kayobe

source ~/kayobe/config/src/kayobe-config/kayobe-env
pip install -e ~/kayobe

kayobe control host bootstrap
kayobe physical network configure --group mgmt-switches