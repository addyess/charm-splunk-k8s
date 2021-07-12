# charm-splunk-k8s

[![charm-splunk-k8s CI](https://github.com/addyess/charm-splunk-k8s/actions/workflows/main.yml/badge.svg)](https://github.com/addyess/charm-splunk-k8s/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/addyess/charm-splunk-k8s/branch/main/graph/badge.svg?token=T27QYE2PCI)](https://codecov.io/gh/addyess/charm-splunk-k8s)

### [![juju](https://assets.ubuntu.com/v1/bbea397b-Logo+no+square.svg)](https://juju.is/ "Juju Operators") Powered by Juju

----------------
Introduction
------------
This charm is used to configure splunk enterprise into a Kubernetes cloud using [juju operators](https://juju.is/ "Juju")

## Deployment
Deploy the app with an attached container resource.
```bash
# Deploy the charm
$ juju deploy splunk-k8s --channel beta
# Approve of the license
$ juju run-action splunk-k8s/0 accept-license
# Deploy the ingress integrator
$ juju deploy nginx-ingress-integrator
# Relate our app to the ingress
$ juju relate splunk-k8s nginx-ingress-integrator
# Set the ingress class
$ juju config nginx-ingress-integrator ingress-class="public"
# Wait for the deployment to complete
$ watch -n1 --color juju status --color
```

## Development
Here's how to get the code, run the tests, and deploy to a local k8s cluster.
```bash
# Clone the charm code
git clone https://github.com/addyess/charm-splunk-k8s && cd charm-splunk-k8s
# Run unit tests
tox -e unit
# Run black on the code
tox -e black
# Run the linter to check for warnings
tox -e lint
# Build the charm package
charmcraft pack
# Deploy to your juju kubernetes model
juju deploy ./splunk-k8s.charm --resource splunk-image=splunk/splunk:latest
```

## Publishing
Publishing the charm through [charmhub.io](https://juju.is/docs/sdk/publishing)
```bash
# Build the charm package
charmcraft pack
# Login to charm store
charmcraft login
# register the charm name
charmcraft splunk-k8s
# upload splunk-k8s.charm and the associated docker image
charmcraft upload splunk-k8s.charm
charmcraft upload-resource splunk-k8s splunk-image --image splunk/splunk:latest
# check the current uploaded version
charmcraft status splunk-k8s
# release charm
charmcraft release splunk-k8s --revision=$REV --resource splunk-image:$RSC_REV --channel=beta
```

----------------
Actions
----------

### Accept-License
Splunk is a licensed software and requires the user accept the license before starting.
The charm requires you to run the action once for the life of the charm. See 
[Splunk Documentation](https://docs.splunk.com/Documentation/Splunk/8.1.3/Admin/HowSplunklicensingworks) 
for more details regarding the license.

### Pause/Resume
This will stop/start the splunk service in the workload container. Due to a bug 
with pebble, the stopping of the service appears to finish quite quickly -- 
but the underlying service doesn't stop for five or more minutes. 

Pause and Resume can be used to work-around this issue. Pause the charm, 
wait 10 minutes, then resume.

```bash
juju run-action splunk-k8s/leader pause
sleep 360
juju run-action splunk-k8s/leader resume
```

### Retrieving the Admin Password
The admin password is necessary to login to splunk, if not configured then 
a password will be automatically generated for you. 
```bash
juju run-action splunk-k8s/leader reveal-admin-password --wait
```

----------------
Config
------

### splunk-license
It is possible to license your splunk by pointing this config to the URL of your
license file.
```bash
juju config splunk-k8s splunk-license='http://internal.example.com/splunk-license'
```

### splunk-password
You can set your own admin password rather than letting the charm auto-generate
one for you.  The charm will block if it doesn't meet the password requirements.
```bash
juju config splunk-k8s splunk-password='my-nifty-password'
```

### splunk-role
This same charm can be used to deploy splunk in various [roles](https://github.com/splunk/splunk-ansible/tree/develop/roles).
```bash
juju config splunk-k8s splunk-role='splunk_indexer'
```

### external-hostname
This is the DNS name used by the kubernetes ingress controller.  By default, 
the DNS name is `splunk.juju` making the web service reachable at http://splunk.juju.

Update to match the DNS settings in your kubernetes deployment. 

-------------------
Road Map
---------

### Relations
* [x] define relations to use ingress controller 
* [ ] define juju relation to splunk forwarders
* [ ] define app relations for HA deployments (password share)

### Configuration
* [ ] Support for license file as well as license URL
