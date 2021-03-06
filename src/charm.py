#!/usr/bin/env python3
# Copyright 2021 Adam Dyess
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import logging
import random
import string
from collections import OrderedDict

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus


logger = logging.getLogger(__name__)

SPLUNK_ARGS = OrderedDict(
    SPLUNK_ROLE="splunk-role",
    SPLUNK_LICENSE_URI="splunk-license",
)


def random_password():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(12, 16)
    return "".join(random.choice(chars) for _ in range(size))


def minimum_password_requirements(password):
    """
    Confirm password is valid, otherwise splunk service silently doesn't start.
    https://docs.splunk.com/Documentation/Splunk/latest/Security/Configurepasswordsinspecfile
    """
    return len(password) >= 8


class SplunkCharm(CharmBase):
    """Charm the service."""

    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.resume_action, self._on_resume_action)
        self.framework.observe(self.on.pause_action, self._on_pause_action)
        self.framework.observe(self.on.splunk_pebble_ready, self._on_pebble_ready)
        self.framework.observe(
            self.on.reveal_admin_password_action, self._on_reveal_admin_password_action
        )
        self.framework.observe(
            self.on.accept_license_action, self._on_accept_license_action
        )
        self.framework.observe(self.on.update_status, self._on_update_status)

        self.state.set_default(license_accepted=False)
        self.state.set_default(pebble_ready=False)
        self.state.set_default(auto_start=True)
        self.state.set_default(last_config_password=None)
        self.state.set_default(splunk_password=random_password())

        self.ingress = IngressRequires(
            self,
            {
                "service-hostname": self.config["external-hostname"],
                "service-name": self.app.name,
                "service-port": 8000,
            },
        )

    def _update_password(self):
        config_password = self.config["splunk-password"]
        last_config_password, self.state.last_config_password = (
            self.state.last_config_password,
            config_password,
        )
        updated = last_config_password != config_password

        if updated:
            if config_password:
                # The user is setting a password
                self.state.splunk_password = config_password
            else:
                # the user is clearing the password
                self.state.splunk_password = random_password()
            logger.info("Splunk Password Updated")

    def _on_accept_license_action(self, _):
        self.state.license_accepted = True
        self._do_config_change()

    def _on_resume_action(self, _):
        self.state.auto_start = True
        self._do_config_change()

    def _on_pause_action(self, _):
        self.state.auto_start = False
        self._do_config_change()

    def _on_pebble_ready(self, event):
        self.state.pebble_ready = True
        self._do_config_change()

    def _on_reveal_admin_password_action(self, action_event):
        return action_event.set_results(
            OrderedDict(username="admin", password=self.state.splunk_password)
        )

    def _on_update_status(self, _):
        container = self.unit.get_container("splunk")
        if not self.state.auto_start:
            self.unit.status = MaintenanceStatus("splunk service is paused")
        elif not container.get_service("splunk").is_running():
            self.unit.status = BlockedStatus("splunk service isn't running")
        else:
            self.unit.status = ActiveStatus("ready")

    def _on_config_changed(self, _):
        """Handle the config-changed event"""
        self.ingress.update_config(
            {"service-hostname": self.config["external-hostname"]}
        )
        self._update_password()
        self._do_config_change()

    def _do_config_change(self):
        if not self.state.pebble_ready:
            self.unit.status = MaintenanceStatus("Awaiting the 'splunk' container")
            return
        if not self.state.license_accepted:
            self.unit.status = BlockedStatus("Run 'accept-license' action")
            return
        if not minimum_password_requirements(self.state.splunk_password):
            self.unit.status = BlockedStatus(
                "Password doesn't meet minimum requirements."
            )
            return

        # Get the splunk container so we can configure/manipulate it
        container = self.unit.get_container("splunk")
        # Create a new config layer
        layer = self._splunk_layer()
        # Get the current config
        services = container.get_plan().to_dict().get("services", {})
        # Check if there are any changes to services
        if services != layer["services"]:
            # Changes were made, add the new layer
            container.add_layer("splunk", layer, combine=True)
            logging.info("Added updated layer 'splunk' to Pebble plan")

        # Stop the service if it is already running
        if container.get_service("splunk").is_running():
            container.stop("splunk")

        # Restart it and report a new status to Juju
        if self.state.auto_start and not container.get_service("splunk").is_running():
            container.start("splunk")
            logging.info("Restarted splunk service")

        # All is well, set an ActiveStatus
        self._on_update_status(None)

    def _splunk_layer(self):
        """Returns a Pebble configuration layer for nrpe-server"""
        environment = {
            "SPLUNK_PASSWORD": self.state.splunk_password,
            "SPLUNK_START_ARGS": "--accept-license",
        }
        for env_name, config in SPLUNK_ARGS.items():
            cfg = self.config[config]
            if cfg:
                environment[env_name] = cfg
        cmd = "bash -c '/sbin/entrypoint.sh start > /var/log/splunk.log 2>&1'"
        return {
            "summary": "splunk layer",
            "description": "pebble config layer for splunk",
            "services": {
                "splunk": {
                    "override": "replace",
                    "summary": "splunk",
                    "command": cmd,
                    "startup": "enabled" if self.state.auto_start else "disabled",
                    "environment": environment,
                },
            },
        }


if __name__ == "__main__":
    main(SplunkCharm, use_juju_for_storage=True)
