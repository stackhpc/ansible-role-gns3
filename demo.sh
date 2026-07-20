git clone https://github.com/L-Chams/kayobe.git -b dellOSfixes ~/kayobe
echo "Kayobe repo cloned"
cd ~/kayobe
mkdir -p config/src
git clone https://opendev.org/openstack/kayobe-config-dev.git config/src/kayobe-config -b master
echo "Kayobe config repo cloned"
sudo ip l add breth1 type bridge
sudo ip l set breth1 up
sudo ip a add 192.168.33.3/24 dev breth1
sudo ip l add dummy1 type dummy
sudo ip l set dummy1 up
sudo ip l set dummy1 master breth1
echo "Bridge and dummy interfaces created"
./dev/install-dev.sh
echo "Kayobe dev environment installed"

cd ~/gns3-ansible-role

source ~/kayobe-venv/bin/activate

ansible-playbook -i inventory.ini trialplaybook.yml -vvv

# copy switch1 file to kayobe config
cp switch1 ~/kayobe/config/src/kayobe-config/etc/kayobe/inventory/host_vars/switch1

groups_file=~/kayobe/config/src/kayobe-config/etc/kayobe/inventory/groups
host="switch1"

if ! awk '/^\[mgmt-switches\]/{flag=1;next}/^\[/{flag=0} flag && $0 == "'"$host"'"' "$groups_file" | grep -q "$host"; then
    sed -i "/^\[mgmt-switches\]$/a ${host}" "$groups_file"
fi

source ~/kayobe-venv/bin/activate
source ~/kayobe/config/src/kayobe-config/kayobe-env

kayobe control host bootstrap
kayobe physical network configure --group mgmt-switches
