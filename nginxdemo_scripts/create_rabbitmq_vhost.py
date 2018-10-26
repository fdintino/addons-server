#!/usr/bin/env python

import json
import os

import lxml.etree
from plumbum.cmd import rabbitmqadmin
from plumbum import cli

__version__ = '1.0.0'


class CreateRabbitMQVhost(cli.Application):
    VERSION = __version__

    username = cli.SwitchAttr(['-u', '--user'], str, default='olympia')
    password = cli.SwitchAttr(['-p', '--pass'], str, default='olympia')
    host = cli.SwitchAttr(['-h', '--host'], str, default="rabbitmq")

    @property
    def args(self):
        return [
            "--format=pretty_json",
            "--host=%s" % self.host,
            "--username=%s" % self.username,
            "--password=%s" % self.password,
        ]

    def rabbitmq_exec(self, *cmds):
        cmd_args = list(cmds) + self.args
        return rabbitmqadmin(*cmd_args)

    def vhost_exists(self, vhost_name):
        vhost_data = json.loads(self.rabbitmq_exec('list', 'vhosts'))
        curr_vhost_names = [vh['name'] for vh in vhost_data]
        return (vhost_name in curr_vhost_names)

    def create_vhost(self, vhost_name):
        self.rabbitmq_exec('declare', 'vhost', 'name=%s' % vhost_name)
        self.rabbitmq_exec(
            'declare', 'permission', 'vhost=%s' % vhost_name,
            'user=olympia', 'read=.*', 'write=.*', 'configure=.*')

    def main(self, vhost_name):
        if not self.vhost_exists(vhost_name):
            self.create_vhost(vhost_name)


def main():
    CreateRabbitMQVhost.run()


if __name__ == '__main__':
    main()
