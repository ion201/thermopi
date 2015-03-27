# thermopi

Python/flask based project to replace a digital thermostat with a raspberry pi to be set via a webui.

TODO:
- Create a service wrapper for GPIO to be started by root with systemd/init. Monitor flags in a /tmp file for managing GPIO output configuration.
- Migrate all globals in Server.py to shared database to allow for simpler mod_wsgi integration.
