set -euo pipefail

echo "STARTING DEMO SCRIPT..."
echo "CLONING KAYOBE REPO..."
git clone https://github.com/L-Chams/kayobe.git -b initFunc
echo "KAYOBE REPO CLONED"
cd ~/kayobe
mkdir -p config/src
echo "CLONING KAYOBE CONFIG REPO..."
git clone https://opendev.org/openstack/kayobe-config-dev.git config/src/kayobe-config -b master
echo "KAYOBE CONFIG REPO CLONED"

# Enable ironic
kolla_file="config/src/kayobe-config/etc/kayobe/kolla.yml"

sed -i 's/^#kolla_enable_ironic:$/kolla_enable_ironic: True/' "$kolla_file"

if grep -q '^kolla_enable_ironic: True$' "$kolla_file"; then
	echo "IRONIC ENABLED IN KOLLA CONFIG"
else
	echo "ERROR: FAILED TO ENABLE IRONIC IN KOLLA CONFIG" >&2
	exit 1
fi

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

# Deploy overcloud
echo "DEPLOYING OVERCLOUD..."
./dev/overcloud-deploy.sh


#Tenks install
echo "INSTALLING TENKS..."
git clone https://opendev.org/openstack/tenks.git
./dev/tenks-deploy-compute.sh ./tenks

# make new bridge for gns3
echo "CREATING GNS3 BRIDGE..."
sudo ovs-vsctl del-port p-tk00-0-ovs
sudo ip l add brgns3 type bridge
sudo ip l set brgns3 up
sudo ip link set dev p-tk00-0-ovs master brgns3

# Environment setup

echo "SETTING UP ENVIRONMENT..."
source ~/kayobe-venv/bin/activate

cd ~/gns3-ansible-role

# # Install GNS3
echo "RUNNING ANSIBLE PLAYBOOK TO INSTALL GNS3..."
ansible-playbook -i inventory.ini trialplaybook.yml -vvv
echo "GNS3 INSTALLED!"




# # copy host_vars for switch to kayobe config
sudo cp ~/gns3-ansible-role/roles/gns3/files/switch1 \
  ~/kayobe/config/src/kayobe-config/etc/kayobe/inventory/host_vars/switch1
cd ~/kayobe/config/src/kayobe-config

git stash


cd ~/kayobe
git fetch https://github.com/L-Chams/kayobe-config-dev NGS
git -c user.name="Automation" \
   -c user.email="automation@localhost" \
   cherry-pick 84b6cd948230134dceb4937d0fe28f19200bd8a9
git cherry-pick 84b6cd948230134dceb4937d0fe28f19200bd8a9



# Add dummy libvirt
sudo cp ~/gns3-ansible-role/roles/gns3/files/dnsmasq /usr/sbin/dnsmasq

source ~/kayobe/config/src/kayobe-config/kayobe-env
pip install -e ~/kayobe


./dev/overcloud-init.sh

kayobe overcloud service deploy --use-test-images

kayobe overcloud host configure

pip install python-openstackclient
pip install python-ironicclient
source ~/kayobe/config/src/kayobe-config/etc/kolla/public-openrc.sh

# Delete demo-router if it exists, provision-net and remake provision-net as vlan type
if openstack router list | grep demo-router; then
  echo "demo-router exists, deleting it..."
  demo_router_port=$(openstack port list --router demo-router -f value -c ID)
  openstack router remove port demo-router $demo_router_port
  openstack router delete demo-router
fi
openstack network delete provision-net

# Generate new provision-net using post configure
kayobe overcloud post configure

# Rstart nova_libvirt if docker container is unhealthy
if  sudo docker ps | grep nova_libvirt | grep unhealthy; then
  echo "nova_libvirt container is unhealthy, restarting it..."
  sudo docker restart nova_libvirt
fi

# Set maintenance mode for baremetal nodes

openstack baremetal node maintenance set red0
openstack baremetal node maintenance set tk0
openstack baremetal node maintenance set tk1


# get switch mac address from host vars file, is like this switch_facts_mac: "{{ switch.mac_address }}"
switch_mac=$(grep switch_facts_mac ~/kayobe/config/src/kayobe-config/etc/kayobe/inventory/host_vars/switch1 | awk '{print $2}')

# Configure tk0 to connect to GNS3
baremetal_port_uuid=$(openstack baremetal port list --node tk0 -f value -c uuid)
openstack baremetal port set  --local-link-connection port_id="Eth 1/1/2" $baremetal_port_uuid
openstack baremetal port set  --local-link-connection switch_id="$switch_mac" $baremetal_port_uuid
openstack baremetal node set --network-interface neutron tk0
openstack baremetal node maintenance unset tk0

# # Create router for .33 and .34
openstack router create provision-router

openstack router add subnet provision-router provision-net
openstack router add subnet provision-router cleaning-net

# Check tk0 is in state available before running test script
tk0_state=$(openstack baremetal node show tk0 -f value -c provision_state)
if [ "$tk0_state" != "available" ]; then
  echo "ERROR: tk0 is not in state 'available', it is in state '$tk0_state'. Please check the node and try again." >&2
  exit 1
fi
# Run test baremetal script
./dev/overcloud-test-baremetal.sh