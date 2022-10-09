# Farm Configuration - Consul

Python scripts and Jupyter Labs notebook for basic management of consul for Braiins OS+ configuration.

## Configuration

Install Jupyter Labs if you don't have it already:

`pip install jupyter lab`

Get basic venv running:

```
python3 -m venv fc-consul-env
source fc-consul-env/bin/activate
pip install -r requirements.txt
```

Add and configure kernel for Jupyter labs:

```
pip install ipykernel
python -m ipykernel install --user --name=fc-consul
```

Let's go:

`jupyter lab`

Open `bos_consul_config.ipynb` and change the kernel in Jupyter Labs UX to `fc-consul-env` (Kernel/Change Kernel)

## Usage
