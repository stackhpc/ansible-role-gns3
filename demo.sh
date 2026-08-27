echo "STARTING DEMO SCRIPT..."
echo "CLONING KAYOBE REPO..."
git clone https://opendev.org/openstack/kayobe.git -b master
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
ovs-vsctl del-port p-tk00-0-ovs
sudo ip l add brgns3 type bridge
sudo ip l set brgns3 up
sudo ip link set dev p-tk00-0-ovs master brgns3

# Environment setup

echo "SETTING UP ENVIRONMENT..."
source ~/kayobe-venv/bin/activate
source ~/kayobe/config/src/kayobe-config/kayobe-env


cd ~/gns3-ansible-role

source ~/kayobe-venv/bin/activate

# Install GNS3
echo "RUNNING ANSIBLE PLAYBOOK TO INSTALL GNS3..."
ansible-playbook -i inventory.ini trialplaybook.yml -vvv
echo "DEMO SCRIPT COMPLETED!"

cd ~/kayobe/config/src/kayobe-config

git cherry-pick 84b6cd948230134dceb4937d0fe28f19200bd8a9
cd -

# Add dummy libvirt
cp gns3-ansible-role/roles/gns3/files/dnsmasq /usr/sbin/dnsmasq


kayobe overcloud service deploy --use-test-images

kayobe overcloud host configure

python3 -m venv os-venv
source os-venv/bin/activate
pip install python-openstackclient
pip install python-ironicclient
source ~/kayobe/config/src/kayobe-config/etc/kolla/public-openrc.sh

# Delete demo-router, provision-net and remake provision-net as vlan type
demo_router_port=$(openstack port list --router demo-router -f value -c ID)
# this will show which port is attached to demo-router
openstack router remove port demo-router demo_router_port
openstack router delete demo-router

openstack network delete provision-net

# Generate new provision-net using post configure
kayobe overcloud post configure




# Set maintenance mode for baremetal nodes

openstack baremetal node maintenance set red0
openstack baremetal node maintenance set tk0
openstack baremetal node maintenance set tk1

# Configure tk0 to connect to GNS3

baremetal_port_uuid=$(openstack baremetal port list --node tk0 -f value -c uuid)
openstack baremetal port set  --local-link-connection port_id="Eth 1/1/2" $baremetal_port_uuid
openstack baremetal port set  --local-link-connection switch_id="$switch_mac" $baremetal_port_uuid
openstack baremetal node set --network-interface neutron tk0
openstack baremetal node maintenance unset tk0

# Create router for .33 and .34

openstack router create provision-router
openstack router add subnet provision-router provision-net
openstack router add subnet provision-router cleaning-net

# Run test baremetal script

./dev/test-baremetal.sh