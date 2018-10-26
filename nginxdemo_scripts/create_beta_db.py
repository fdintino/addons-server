#!/usr/bin/env python

import sys
import os

import lxml.etree
from plumbum.cmd import mysql, make
from plumbum import cli, local, FG

__version__ = '1.0.0'


root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class CreateBetaDB(cli.Application):
    VERSION = __version__

    user = cli.SwitchAttr(['-u', '--user'], str, default='root')
    host = cli.SwitchAttr(['-h', '--host'], str, default="mysqld")

    @property
    def args(self):
        return ["-ss", "-h%s" % self.host, "-u%s" % self.user, "--protocol=tcp"]

    def mysql_exec(self, cmd, db=None, keys=True, flat=False, *args):
        args = self.args + list(args) + ["--xml", "-e", cmd]
        if db is not None:
            args += [db]
        output = mysql(args).strip()
        if not output:
            return
        tree = lxml.etree.fromstring(output)
        rows = tree.xpath("//row")
        data = []
        for row in rows:
            fields = row.xpath(".//field")
            row_data = {} if keys else []
            if flat and len(fields) > 1:
                raise Exception("flat=True only works when a single column is selected")
            if flat:
                row_data = fields[0].text
            else:
                for field in fields:
                    if keys:
                        row_data[field.attrib['name']] = field.text
                    else:
                        row_data.append(field.text)

            data.append(row_data)
        return data

    def db_exists(self, db_name):
        return bool(self.mysql_exec('SHOW DATABASES LIKE "%s"' % db_name, flat=True))

    def create_db(self, db_name):
        self.mysql_exec("CREATE DATABASE %s" % db_name)
        with local.cwd(root_dir):
            make['-f', 'Makefile-docker', 'initialize_db'] & FG
            make['-f', 'Makefile-docker', 'populate_data'] & FG

    def main(self, db_name):
        if not self.db_exists(db_name):
            self.create_db(db_name)
            sys.exit(1)
        else:
            sys.exit(0)


def main():
    CreateBetaDB.run()


if __name__ == '__main__':
    main()
