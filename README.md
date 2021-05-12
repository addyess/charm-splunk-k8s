# charm-splunk-k8s

[![charm-splunk-k8s CI](https://github.com/addyess/charm-splunk-k8s/actions/workflows/main.yml/badge.svg)](https://github.com/addyess/charm-splunk-k8s/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/addyess/charm-splunk-k8s/branch/main/graph/badge.svg?token=T27QYE2PCI)](https://codecov.io/gh/addyess/charm-splunk-k8s)

Introduction
============

This charm is used to configure splunk enterprise into a kubernetes cloud

Deployment
==========
Deploy the app with an attached container resource
```bash
# Deploy the charm
$ juju deploy splunk-k8s --resource splunk-image=splunk/splunk:latest
# Approve of the license
$ juju run-action splunk-k8s accept-license --wait
# Deploy the ingress integrator
$ juju deploy nginx-ingress-integrator
# Relate our app to the ingress
$ juju relate splunk-k8s nginx-ingress-integrator
# Set the ingress class
$ juju config nginx-ingress-integrator ingress-class="public"
# Add an entry to /etc/hosts
$ echo "127.0.0.1 splunk.juju" | sudo tee -a /etc/hosts
# Wait for the deployment to complete
$ watch -n1 --color juju status --color

```

Development
===========
```bash
# Clone the charm code
git clone https://github.com/addyess/charm-splunk-k8s && cd charm-splunk-k8s
# Run unit tests
tox -e unit
# Run black on the code
tox -e black
# Build the charm package
charmcraft pack
# Deploy!
juju deploy splunk-k8s --resource splunk-image=splunk/splunk:latest
# Approve of the license
juju run-action splunk-k8s accept-license --wait
```

Retrieving the Admin Password
============================
```bash
juju run -u splunk-k8s/leader -- cat /var/run/secrets/splunk/passwd
```