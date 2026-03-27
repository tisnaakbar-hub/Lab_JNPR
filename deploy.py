import yaml
from jinja2 import Template
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

# 1. Load Data
try:
    with open('nodes.yml') as f:
        data = yaml.safe_load(f)
    with open('junos_template.j2') as f:
        tmpl = Template(f.read())
except FileNotFoundError as e:
    print(f"File tidak ditemukan: {e}")
    exit()

all_lb = [n['loopback'].split('/')[0] for n in data['nodes']]

# 2. Loop per Router
for node in data['nodes']:
    print(f"\n>>> Mengonfigurasi {node['name']} ({node['mgmt']})...")

    # Render template dan bersihkan baris kosong/spasi berlebih
    conf_set = tmpl.render(
        name=node['name'],
        loopback=node['loopback'],
        interfaces=node['interfaces'],
        all_loopbacks=all_lb
    ).strip()

    # 3. Push via NETCONF
    # Gunakan 4 spasi untuk setiap level indentasi
    dev = Device(host=node['mgmt'], user="admin", passwd="admin@123")
    try:
        dev.open()
        with Config(dev, mode='exclusive') as cu:
            print(f"Loading configuration to {node['name']}...")
            cu.load(conf_set, format='set')

            if cu.diff():
                print("Perubahan terdeteksi, melakukan commit...")
                cu.commit(comment="Fixing Indentation and Unknown Command")
                print(f"SUCCESS: {node['name']} terkonfigurasi.")
            else:
                print(f"SKIP: {node['name']} sudah sinkron.")
        dev.close()
    except Exception as e:
        print(f"ERROR pada {node['name']}: {e}")
        if dev.connected:
            dev.close()
