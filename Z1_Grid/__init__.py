# -*- coding: utf-8 -*-
# Z1_Grid - punto de entrada del remote script.
# Live importa este archivo y llama a create_instance().
# Sintaxis Python 2.5 conservadora: sin with, sin comprensiones de dict,
# sin literales de conjunto, sin ternarios.

from Z1_Grid import Z1_Grid


def create_instance(c_instance):
    return Z1_Grid(c_instance)
