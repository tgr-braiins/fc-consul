# Farm Configuration - Consul

Python scripts and Jupyter Labs notebook for basic management of consul for Braiins OS+ configuration. Tested on Ubuntu 22.04.

## Configuration

Install Jupyter Labs if you don't have it already:

`pip install jupyter lab`

Get the repo:

```
git clone https://github.com/tgr-braiins/fc-consul.git
cd ./fc-consul
```

Get basic venv running:

```
python3 -m venv fc-consul-env
source fc-consul-env/bin/activate
pip install -r requirements.txt
```

Add and configure kernel for Jupyter labs:

```
pip install ipykernel
python -m ipykernel install --user --name=fc-consul-env
```

Let's go:

`jupyter lab`

Open `bos_consul_config.ipynb` and change the kernel in Jupyter Labs UX to `fc-consul-env` (Kernel/Change Kernel)

## Usage
### Inventory Management
Two functions are available for inventory management, `modify_inventory` and `get_inventory`

#### Load/Update Inventory
To load or update inventory from CSV file, text file, or any other structured file, you will first need to get the file to pandas data frame. For CSV file (example `inventory.csv` is available) you can use:

```
inventory = pd.read_csv('./inventory.csv')
```

As a next step, you have to define consul URL where inventory should be uploaded:

```
consul_url = 'http://localhost:8500'
```

Finally, you can load your inventory using `modify_inventory` function:

```
cs.modify_inventory(inventory, 'set', consul_url)
```
See Modify Inventory for description of all parameters of the function.

#### Delete Inventory for Known MAC Addresses
To delete inventory from Consul, use `modify_inventory` function with verb `delete`. It will use the mac address column in the supplied data frame.

```
cs.modify_inventory(inventory, 'delete', consul_url)
```

This function will always delete the entire key, it cannot be used to update the values for existing MAC address that already exists in Consul. Use `set` if you want to update inventory.

#### Delete Entire Inventory
To delete entire inventory use:

```
modify_inventory(verb='delete_all', consul_url=consul_url)
```

#### Get inventory
You can load inventory defined in Consul to pandas data farme using `get_inventory()` function. The only useful argument is `consul_url`:

```
 get_inventory(consul_url)
```

#### Modify Inventory

```
  modify_inventory (
	inventory = None, 
	verb = None, 
	consul_url = None, 
	cols = None, 
	mac_addr_col = 'mac', 
	inventory_endpoint = 'v1/kv/inventory/bos%2B'
	)
```

 - `inventory` - pandas data frame containing at least mac address and one additional attribute
 - `verb` - `set` to load data, `delete` to delete data based on mac addresses in pandas data frame, `delete_all` to delete all records in inventory
 - `consul` - consul instance url
 - `cols` - list of columns to be loaded as inventory; by default, all columns are uploaded
 - `mac_addr_col` - name of the column containing mac address
 - `inventory_endpoint` - internal, no need to use
