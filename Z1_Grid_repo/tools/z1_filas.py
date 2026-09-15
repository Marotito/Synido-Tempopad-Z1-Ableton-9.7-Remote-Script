#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
z1_filas.py  -  medicion de colores del Synido TempoPAD Z-1, metodo por FILAS

Cada foto muestra:
  - FILA DE ARRIBA : los 8 valores que se estan midiendo (izq -> der)
  - FILA DE ABAJO  : el numero de pasada en BINARIO (blanco = 1)
                     + ancla blanca fija en la esquina inferior derecha

Asi cada foto se identifica sola y se lee sin ambiguedad.

    pip3 install mido python-rtmidi

    python3 z1_filas.py plan                  imprime las 16 pasadas
    python3 z1_filas.py ports                 lista puertos MIDI
    python3 z1_filas.py fila N --port X       pasada N (1..16)
    python3 z1_filas.py off --port X          apaga todo

Z-1 en USER MODE, Ableton cerrado.
"""
import sys, time

CANAL = 2
PAUSA = 0.008
BLANCO = 3            # valor del ancla y de los bits (medido antes)
POR_PASADA = 8
PASADAS = 16
BITS = 5              # 16 pasadas entran en 5 bits


def nota_de(columna, fila):
    """fila 0 = fila de arriba"""
    return 36 + 32 * (columna // 4) + (7 - fila) * 4 + (columna % 4)


def valores_de(pasada):
    base = (pasada - 1) * POR_PASADA + 1
    return [v for v in range(base, base + POR_PASADA) if v <= 127]


def mensajes(pasada):
    """[(nota, velocity)] de la pasada, incluyendo etiqueta y ancla."""
    m = []
    # fila de arriba: los valores medidos
    for i, v in enumerate(valores_de(pasada)):
        m.append((nota_de(i, 0), v))
    # fila de abajo: numero de pasada en binario, MSB a la izquierda
    for b in range(BITS):
        encendido = (pasada >> (BITS - 1 - b)) & 1
        if encendido:
            m.append((nota_de(b, 7), BLANCO))
    # ancla fija: esquina inferior derecha
    m.append((nota_de(7, 7), BLANCO))
    return m


def tabla(pasada):
    vs = valores_de(pasada)
    bits = ''.join(str((pasada >> (BITS - 1 - b)) & 1) for b in range(BITS))
    l = []
    l.append('  PASADA %d/%d      etiqueta binaria: %s' % (pasada, PASADAS, bits))
    l.append('  fila de arriba, de izquierda a derecha:')
    l.append('     col:  ' + ''.join('%6d' % c for c in range(8)))
    l.append('     nota: ' + ''.join('%6d' % nota_de(c, 0) for c in range(8)))
    l.append('     VEL:  ' + ''.join('%6s' % (vs[c] if c < len(vs) else '-')
                                     for c in range(8)))
    return '\n'.join(l)


def imprimir_plan():
    print('=' * 60)
    print(' MEDICION POR FILAS  -  Synido TempoPAD Z-1')
    print('=' * 60)
    print()
    print(' Fila de ARRIBA  = los 8 valores medidos (izquierda a derecha)')
    print(' Fila de ABAJO   = numero de pasada en binario (5 pads blancos)')
    print('                   + ancla blanca fija abajo a la derecha')
    print()
    print(' Sacar las fotos desde arriba, lo mas de frente posible.')
    print(' Misma luz y misma distancia en las 16.')
    print()
    for p in range(1, PASADAS + 1):
        print(tabla(p))
        print()
    total = sum(len(valores_de(p)) for p in range(1, PASADAS + 1))
    print(' cobertura: %d valores (1..127)' % total)


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
    el = None
    for s in outs:
        if nombre.lower() in s.lower(): el = s; break
    if el is None:
        print('No encuentro puerto con: %s' % nombre)
        for s in outs: print('   ' + s)
        sys.exit(1)
    print('puerto: %s' % el)
    return mido.open_output(el), mido


def enviar(p, mido, nota, vel):
    p.send(mido.Message('note_on', channel=CANAL, note=nota, velocity=vel))
    time.sleep(PAUSA)


def apagar(p, mido):
    for n in range(36, 108):
        enviar(p, mido, n, 0)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    if cmd == 'plan':
        imprimir_plan(); return
    if cmd == 'ports':
        try:
            import mido
        except ImportError:
            print('Falta mido:  pip3 install mido python-rtmidi'); return
        print('SALIDAS:');  [print('  ' + s) for s in mido.get_output_names()]
        print('ENTRADAS:'); [print('  ' + s) for s in mido.get_input_names()]
        return

    puerto = None
    if '--port' in a:
        i = a.index('--port')
        if i + 1 < len(a): puerto = a[i + 1]
    p, mido = abrir(puerto)
    try:
        if cmd == 'off':
            apagar(p, mido); print('apagado.'); return
        if cmd != 'fila':
            print('comando desconocido: %s' % cmd); return
        n = int(a[1])
        if n < 1 or n > PASADAS:
            print('pasada fuera de rango (1..%d)' % PASADAS); return
        apagar(p, mido)
        for nota, vel in mensajes(n):
            enviar(p, mido, nota, vel)
        print()
        print(tabla(n))
        print()
        print('Sacale la foto de frente. Despues:  python3 z1_filas.py fila %d --port "%s"'
              % (n + 1 if n < PASADAS else 1, puerto or ''))
    finally:
        p.close()


if __name__ == '__main__':
    main()
