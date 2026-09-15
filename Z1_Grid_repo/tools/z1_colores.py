#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
z1_colores.py  -  medicion de la paleta del Synido TempoPAD Z-1

Corre desde Catalina, sin Ableton. Enciende los LEDs mandando
note-on en canal MIDI 3 y te deja fotografiar el resultado.

    pip3 install mido python-rtmidi

Uso:
    python3 z1_colores.py ports              lista los puertos MIDI
    python3 z1_colores.py plan               imprime el plan completo (sin MIDI)
    python3 z1_colores.py pads N   --port X  pasada N de pads (1..5)
    python3 z1_colores.py sides N  --port X  pasada N de laterales (1..8)
    python3 z1_colores.py off      --port X  apaga todo

El Z-1 tiene que estar en USER MODE. Ableton cerrado.

METODO
------
Pads: damero fijo de 32 pads (los vecinos quedan apagados para que
no se contamine el color). De esos 32, TRES son anclajes con valor
fijo en todas las pasadas: sirven para detectar si la camara cambio
el balance de blancos entre fotos. Quedan 29 valores por pasada,
5 pasadas cubren 1..127.

Laterales: los 8 botones llevan valores impares, 8 por pasada,
8 pasadas = los 64 impares de 1 a 127. Los anclajes de pads quedan
encendidos tambien en estas fotos, asi no hay que sacrificar
ningun boton lateral.
"""

import sys
import time

CANAL = 2            # canal MIDI 3 (0-based)
PAUSA = 0.006        # entre mensajes, para no perder ninguno en rafaga

NOTAS_LATERALES = [100, 101, 102, 103, 104, 105, 106, 107]
NOMBRES_LATERALES = ['Octave', 'Transpose', 'Velocity', 'Light',
                     'MMC', 'Stop', 'Play', 'Record']

# anclajes: (columna, fila, valor).  fila 0 = arriba
ANCLAJES = [(0, 0, 3),    # blanco, arriba izquierda
            (7, 1, 21),   # verde,  arriba derecha
            (0, 6, 41)]   # azul,   abajo izquierda


def nota_de(columna, fila):
    """Nota MIDI del pad. fila 0 = fila de arriba."""
    return 36 + 32 * (columna // 4) + (7 - fila) * 4 + (columna % 4)


def damero():
    """Los 32 pads del damero, en orden de lectura (arriba->abajo,
    izquierda->derecha)."""
    r = []
    for fila in range(8):
        for col in range(8):
            if (col + fila) % 2 == 0:
                r.append((col, fila))
    return r


def posiciones_de_valores():
    """Los pads del damero que NO son anclaje."""
    anc = set((c, f) for c, f, _ in ANCLAJES)
    return [p for p in damero() if p not in anc]


VALORES_POR_PASADA = len(posiciones_de_valores())     # 29
PASADAS_PADS = 5


def plan_pads(pasada):
    """Devuelve dict {(col,fila): valor} para una pasada (1..5).
    Incluye los anclajes."""
    if pasada < 1 or pasada > PASADAS_PADS:
        raise ValueError('pasada de pads fuera de rango (1..%d)' % PASADAS_PADS)
    libres = posiciones_de_valores()
    primero = (pasada - 1) * VALORES_POR_PASADA + 1
    m = {}
    for c, f, v in ANCLAJES:
        m[(c, f)] = v
    for i, pos in enumerate(libres):
        valor = primero + i
        if valor <= 127:
            m[pos] = valor
    return m


def plan_sides(pasada):
    """Devuelve dict {nota: valor} para una pasada de laterales (1..8)."""
    if pasada < 1 or pasada > 8:
        raise ValueError('pasada de laterales fuera de rango (1..8)')
    m = {}
    for i, nota in enumerate(NOTAS_LATERALES):
        indice = (pasada - 1) * 8 + i
        m[nota] = 1 + 2 * indice          # impares 1..127
    return m


# ------------------------------------------------------------------
#  impresion del plan (no necesita MIDI ni mido)
# ------------------------------------------------------------------
def tabla_pads(pasada):
    m = plan_pads(pasada)
    anc = dict(((c, f), v) for c, f, v in ANCLAJES)
    lineas = []
    lineas.append('  PASADA DE PADS %d/%d' % (pasada, PASADAS_PADS))
    lineas.append('  (fila de arriba primero;  .  = apagado;  A = anclaje)')
    lineas.append('     ' + ''.join('%6s' % ('c%d' % c) for c in range(8)))
    for fila in range(8):
        celdas = []
        for col in range(8):
            if (col, fila) in anc:
                celdas.append('%6s' % ('A' + str(anc[(col, fila)])))
            elif (col, fila) in m:
                celdas.append('%6d' % m[(col, fila)])
            else:
                celdas.append('%6s' % '.')
        lineas.append('  f%d ' % fila + ''.join(celdas))
    usados = [v for k, v in m.items() if (k[0], k[1]) not in anc]
    if usados:
        lineas.append('  valores medidos en esta pasada: %d a %d'
                      % (min(usados), max(usados)))
    return '\n'.join(lineas)


def tabla_sides(pasada):
    m = plan_sides(pasada)
    lineas = []
    lineas.append('  PASADA DE LATERALES %d/8' % pasada)
    lineas.append('  (los 3 anclajes de pads quedan encendidos)')
    for i, nota in enumerate(NOTAS_LATERALES):
        lineas.append('    %-10s nota %3d  ->  velocity %3d'
                      % (NOMBRES_LATERALES[i], nota, m[nota]))
    return '\n'.join(lineas)


def imprimir_plan():
    print('=' * 64)
    print(' PLAN DE MEDICION  -  Synido TempoPAD Z-1')
    print('=' * 64)
    print()
    print(' Anclajes fijos en TODAS las fotos:')
    for c, f, v in ANCLAJES:
        print('   col %d fila %d  ->  nota %3d  velocity %3d'
              % (c, f, nota_de(c, f), v))
    print()
    print(' Si un anclaje se ve distinto entre dos fotos, la diferencia')
    print(' es de la camara y no del aparato: normalizar antes de leer.')
    print()
    for p in range(1, PASADAS_PADS + 1):
        print(tabla_pads(p))
        print()
    for p in range(1, 9):
        print(tabla_sides(p))
        print()
    total_pads = sum(len([v for k, v in plan_pads(p).items()
                          if (k[0], k[1]) not in
                          set((c, f) for c, f, _ in ANCLAJES)])
                     for p in range(1, PASADAS_PADS + 1))
    print(' cobertura pads: %d valores (1..127)' % min(total_pads, 127))
    print(' cobertura laterales: 64 valores impares (1..127)')


# ------------------------------------------------------------------
#  envio MIDI
# ------------------------------------------------------------------
def abrir_puerto(nombre):
    try:
        import mido
    except ImportError:
        print('Falta mido. Instalalo con:')
        print('   pip3 install mido python-rtmidi')
        sys.exit(1)
    salidas = mido.get_output_names()
    if not nombre:
        print('Indica el puerto con --port. Disponibles:')
        for s in salidas:
            print('   ' + s)
        sys.exit(1)
    elegido = None
    for s in salidas:
        if nombre.lower() in s.lower():
            elegido = s
            break
    if elegido is None:
        print('No encuentro un puerto que contenga: %s' % nombre)
        print('Disponibles:')
        for s in salidas:
            print('   ' + s)
        sys.exit(1)
    print('puerto: %s' % elegido)
    return mido.open_output(elegido), mido


def enviar(puerto, mido, nota, velocity):
    puerto.send(mido.Message('note_on', channel=CANAL,
                             note=nota, velocity=velocity))
    time.sleep(PAUSA)


def apagar_todo(puerto, mido):
    for nota in range(36, 100):
        enviar(puerto, mido, nota, 0)
    for nota in NOTAS_LATERALES:
        enviar(puerto, mido, nota, 0)


def listar_puertos():
    try:
        import mido
    except ImportError:
        print('Falta mido. Instalalo con:')
        print('   pip3 install mido python-rtmidi')
        sys.exit(1)
    print('SALIDAS MIDI:')
    for s in mido.get_output_names():
        print('   ' + s)
    print()
    print('ENTRADAS MIDI:')
    for s in mido.get_input_names():
        print('   ' + s)


# ------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]

    if cmd == 'plan':
        imprimir_plan()
        return
    if cmd == 'ports':
        listar_puertos()
        return

    puerto_nombre = None
    if '--port' in args:
        i = args.index('--port')
        if i + 1 < len(args):
            puerto_nombre = args[i + 1]

    puerto, mido = abrir_puerto(puerto_nombre)
    try:
        if cmd == 'off':
            apagar_todo(puerto, mido)
            print('todo apagado.')
            return

        if cmd not in ('pads', 'sides'):
            print('comando desconocido: %s' % cmd)
            return
        if len(args) < 2:
            print('falta el numero de pasada.')
            return
        pasada = int(args[1])

        apagar_todo(puerto, mido)

        if cmd == 'pads':
            m = plan_pads(pasada)
            for (col, fila), valor in sorted(m.items()):
                enviar(puerto, mido, nota_de(col, fila), valor)
            print()
            print(tabla_pads(pasada))
        else:
            # anclajes de pads encendidos como referencia de camara
            for c, f, v in ANCLAJES:
                enviar(puerto, mido, nota_de(c, f), v)
            m = plan_sides(pasada)
            for nota, valor in sorted(m.items()):
                enviar(puerto, mido, nota, valor)
            print()
            print(tabla_sides(pasada))

        print()
        print('Sacale la foto. Cuando termines:')
        print('   python3 z1_colores.py off --port "%s"' % (puerto_nombre or ''))
    finally:
        puerto.close()


if __name__ == '__main__':
    main()
