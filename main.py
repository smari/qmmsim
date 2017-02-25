#!/usr/bin/python
"""
QMM: Quarterly Macroeconomic Model of the Icelandic Economy

See README.md for details.
"""

import click
import csv
from simulation import Simulation
from parser import AbaqusParser

@click.command()
@click.argument("database", type=click.File())
def cli(database):
    if database.name[-3:] != "csv":
        print "We only know how to handle CSV databases for now."
        return False

    reader = csv.DictReader(database)
    db = {}
    for row in reader:
        for k, v in row.iteritems():
            if not k in db:
                db[k] = []
            db[k].append(v)

    simulation = Simulation(db)
    parser = AbaqusParser(simulation)
    parser.debug = True
    #res = parser.parse_file("sedlabanki/qmm_likan_desember_2015.inp")
    #if not res:
    #    simulation.handle_errors()
    #    return False
    #res = parser.parse_file("sedlabanki/qmm_stikur_desember_2015.inp")
    #if not res:
    #    simulation.handle_errors()
    #    return False

    res = parser.parse_file("test/test.inp")
    if not res:
        simulation.handle_errors()
        #return False

    print "PI(440) = ", simulation.get_value('PI', 440)
    print "OneToTen(4) = ", simulation.get_value('OneToTen', 4)


if __name__=="__main__":
    cli()
