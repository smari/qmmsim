#!/usr/bin/python
"""
QMM: Quarterly Macroeconomic Model of the Icelandic Economy

See README.md for details.
"""

import click

from simulation import Simulation
from parser import AbaqusParser

@click.command()
def cli():
    simulation = Simulation()
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
        return False


if __name__=="__main__":
    cli()
