#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
z1_parpadeo.py  -  probar si el Z-1 soporta parpadeo y pulso por canal

El Launchpad no programa el parpadeo: lo PIDE por canal MIDI.
   canal 1 (indice 0) -> luz fija
   canal 2 (indice 1) -> BLINK   (parpadeo)
   canal 3 (indice 2) -> PULSE   (latido)
Nosotros venimos usando el indice 2 y vemos luz FIJA, asi que el Z-1
no usa el mismo reparto. Este script barre los 16 canales para ver
cual hace que, si es que alguno hace algo.

    python3 z1_parpadeo.py ports
    python3 z1_parpadeo.py barrido --port X    un pad por canal, mismo color
    python3 z1_parpadeo.py canal N --port X    solo el canal N (1..16)
    python3 z1_parpadeo.py off --port X

Z-1 en USER MODE, Ableton cerrado.
"""
import sys, time

NOTA_BASE = 36
PAUSA = 0.01
COLOR = 21          # verde pleno: facil de ver latir


def nota_de(col, fila):
    return 36 + 32 * (col // 4) + (7 - fila) * 4 + (col % 4)


def abrir(nombre):
    try:
        import mido
    except ImportError:
        print('Falta mido:  pip3 install mido python-rtmidi'); sys.exit(1)
    outs = mido.get_output_names()
    if not nombre:
        print('Falta --port. Disponibles:')
        for s in outs: print('   ' + s)
        sys.exit(1)
    for s in outs:
        if nombre.lower() in s.lower():
            print('puerto: %s' % s)
            return mido.open_output(s), mido
    print('No encuentro: %s' % nombre)
    for s in outs: print('   ' + s)
    sys.exit(1)


def enviar(p, mido, canal, nota, vel):
    p.send(mido.Message('note_on', channel=canal, note=nota, velocity=vel))
    time.sleep(PAUSA)


def apagar(p, mido):
    for canal in range(16):
        for n in range(36, 108):
            p.send(mido.Message('note_on', channel=canal, note=n, velocity=0))
    time.sleep(0.2)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    if a[0] == 'ports':
        import mido
        print('SALIDAS:'); [print('  '+s) for s in mido.get_output_names()]
        return
    puerto = None
    if '--port' in a:
        i = a.index('--port')
        if i+1 < len(a): puerto = a[i+1]
    p, mido = abrir(puerto)
    try:
        if a[0] == 'off':
            apagar(p, mido); print('apagado.'); return

        if a[0] == 'barrido':
            apagar(p, mido)
            print()
            print('Un pad por canal, todos verde (velocity %d).' % COLOR)
            print('La fila de arriba son los canales 1 a 8,')
            print('la segunda fila los canales 9 a 16.')
            print()
            for canal in range(16):
                fila = 0 if canal < 8 else 1
                col = canal % 8
                enviar(p, mido, canal, nota_de(col, fila), COLOR)
                print('   canal %2d  ->  fila %d, columna %d  (nota %d)'
                      % (canal+1, fila+1, col+1, nota_de(col, fila)))
            print()
            print('MIRA EL APARATO 10 SEGUNDOS y anota:')
            print('  - que pads se encienden')
            print('  - si ALGUNO parpadea o late en vez de quedar fijo')
            return

        if a[0] == 'canal':
            canal = int(a[1]) - 1
            apagar(p, mido)
            for col in range(8):
                enviar(p, mido, canal, nota_de(col, 0), COLOR)
            print()
            print('Canal MIDI %d, fila de arriba, verde.' % (canal+1))
            print('Fijate si queda fija, parpadea o late.')
            return
        print('comando desconocido')
    finally:
        p.close()


if __name__ == '__main__':
    main()
