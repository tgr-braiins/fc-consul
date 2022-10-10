import requests
import pandas as pd
from io import StringIO
import base64
import urllib.parse
import time
import json
import numpy as np

# Create/Update/Delete keys
def modify_inventory(inventory = None, verb = None, consul_url = None, cols = None, mac_addr_col = 'mac', inventory_endpoint = 'v1/kv/inventory/bos%2B'):
    start_time = time.time()
    
    if cols is None and verb != 'delete_all':
        cols = [col for col in inventory.columns if col not in [mac_addr_col]]
    if verb != 'delete_all':
        mac_addrs = inventory[mac_addr_col].values

    # Transform row of dataframe into json, handle overrides
    def prep(x):
        x = x[x.notnull()].to_dict()
        data = {}
        if 'config_path' in x and not pd.isna(x['config_path']):
                data['overrides'] = {"config_path":x['config_path']}
        if 'config_path' in x:
            del x['config_path']
        data["items"] = x
        json_data = json.dumps(data)
        return json_data
    
    # Generate appropriate oprations    
    operations = []
    if verb == 'set':
        # individual values are wrapped in "items"
        vals = inventory[cols].apply(lambda x: prep(x), axis=1).values
        operations = operations + [{"KV":{"Verb":verb,"Key": '/'.join(['inventory','bos+', mac_addr]), 
                         "Value": base64.b64encode(bytes(val, 'utf-8')).decode('utf-8')}} for mac_addr, val in zip(mac_addrs, vals)]
    elif verb == 'delete':
        operations = operations + [{"KV":{"Verb":verb,"Key": '/'.join(['inventory','bos+', mac_addr])}} for mac_addr in mac_addrs]
    elif verb == 'delete_all':
        keys = requests.get('/'.join([consul_url,inventory_endpoint,'?keys'])).json()
        operations = operations + [{"KV":{"Verb":"delete","Key": key}} for key in keys if not key.endswith('/')]
        
    # Execute in batches by 64 operations (max consul supports
    i=0
    while i < len(operations):
        requests.put('/'.join([consul_url,'v1/txn']), data = json.dumps(operations[i:i+64]))
        i = i+64
    print("Dur (keys management):", time.time() - start_time)

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def get_inventory(consul_url = 'http://localhost:8500', inventory_endpoint = 'v1/kv/inventory/bos%2B'):
    """Get inventory
    consul_url = 'http://localhost:8500'
    inventory_endpoint = 'v1/kv/inventory/bos%2B'
    Returns dataframe with inventory data that are defined in consul.
    """    
    start_time = time.time()
    # Get list of all keys
    keys = requests.get('/'.join([consul_url,inventory_endpoint,'?keys'])).json()
    # Operations that will be sent to consul. Excluding folders (ending with '/')
    operations = [{"KV":{"Verb":"get","Key":key}} for key in keys if not key.endswith('/')]

    # Read keys in batch. Using consul transactions that are limited to 64 operations in one call.
    results = []; i=0
    while i < len(operations):
        batch_res = [result["KV"] for result in requests.put('/'.join([consul_url,'v1/txn']), data = json.dumps(operations[i:i+64])).json()["Results"]]
        results = results + batch_res
        i = i + 64
    
    # Decode base64 value
    [res.update({'Value':base64.b64decode(res['Value']).decode('UTF-8')}) for res in results]
    # Replace non-json values with invalid status
    [res.update({'Value':'{"items":{"status":"invalid"}}'}) for res in results if not is_json(res['Value'])]

    df = pd.DataFrame(results)

    # Expand JSON in Value to columns and join in back
    df = df.join(df.Value.apply(lambda x: pd.Series(json.loads(x),dtype="object")))
    df = df.join(df['items'].apply(pd.Series))
    
    # Process overrides
    if 'overrides' in df.columns:
        x  = df['overrides'].apply(pd.Series)           # expand json
        if len(x.columns) > 1:                          # drop second column (strange expansion of NaN values, obviously works only if 1 value is expected
            x  = x.drop(x.columns[1], axis=1)
        df = df.join(x, lsuffix='_left')                # add config template from overrides back

    # This is assuming the path starts with two levels like inventory/bos
    df['mac'] = df['Key'].str.split('/').str[2]
    # Remove columns we don't need
    drop_cols = [col for col in df.columns if col in ['LockIndex','Flags','Value','CreateIndex','ModifyIndex','Key','items', 'overrides', '0_left', '0']]
    df = df.drop(drop_cols, axis=1)

    print("Dur (get inventory):", str(time.time() - start_time))
    return df


def get_instances(consul_url, node):
    # Instances for bos+ service
    services_endpoint = '/'.join([consul_url, 'v1/catalog/service/bos+'])
    kv_endpoint = '/'.join([consul_url, 'v1/kv'])
    kv_endpoint_ux = '/'.join([consul_url, 'ui', node, 'kv'])
    instances = requests.get(services_endpoint).json()
    out = []
    for instance in instances:
        raw_path = '/'.join((instance['ServiceMeta']['config_path'].split('/'))[4:]) # there is duplicate /bos+/conf at the beginning
        status_path = urllib.parse.quote('/'.join(['running/bos+', raw_path, instance['ServiceID'].lower(), 'status']))
        config_path = urllib.parse.quote('/'.join(['running/bos+', raw_path, instance['ServiceID'].lower(), 'conf']))
        # API URLs
        full_status_url = '/'.join([kv_endpoint, status_path])
        full_config_url = '/'.join([kv_endpoint, config_path])
        # UX URLs
        full_status_url_ux = '/'.join([kv_endpoint_ux, status_path, 'edit'])
        full_config_url_ux = '/'.join([kv_endpoint_ux, config_path, 'edit'])        
        full_tempplate_url_ux = '/'.join([kv_endpoint_ux,'conf/bos+', raw_path, 'edit'])
        status = ''
        try:
            status = requests.get('/'.join([kv_endpoint, status_path])).json()[0]['Value']
        except:
            pass
        status_decoded = base64.b64decode(status.encode('ascii')).decode('ascii')
        out.append(([full_config_url_ux,
                     full_status_url_ux,
                     full_tempplate_url_ux,
                     instance['Address'],
                     instance['ServiceID'].lower(),
                     instance['ServiceMeta']['server_version'],
                     instance['ServiceAddress'],
                     status_decoded]))
    df_instances = pd.DataFrame(out, columns = ['config_url', 'status_url', 'template_url', 'address','service_id', 'server_version', 'service_address', 'status'])
    return df_instances

def merge_inventory_instances(df_inventory, df_instances):
    df_out = pd.merge(df_inventory,df_instances,left_on='mac', right_on='service_id',how='outer')


    def make_clickable(url, name):
        return '<a href="{}" rel="noopener noreferrer" target="_blank">{}</a>'.format(url,name)

    df_out['config_link'] = df_out.apply(lambda x: make_clickable(x['config_url'], 'config'), axis=1)
    df_out['status_link'] = df_out.apply(lambda x: make_clickable(x['status_url'], 'status'), axis=1)
    df_out['template_link'] = df_out.apply(lambda x: make_clickable(x['template_url'], 'template'), axis=1)
    return df_out