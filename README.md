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
