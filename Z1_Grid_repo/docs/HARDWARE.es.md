# Synido TempoPAD Z-1 — referencia de hardware

*[English version](HARDWARE.md)*

Todo lo que está acá fue medido sobre el hardware real o leído de los
propios scripts decompilados de Ableton. Donde algo es una inferencia y no
una verificación, está dicho.

Si estás escribiendo tu propio script para este aparato, o para otro clon de
Launchpad, esta es la parte que vale la pena leer.

---

## 1. Modos y canales MIDI

El Z-1 tiene cinco modos de hardware, que se eligen con los botones de
arriba de la grilla. El canal por el que transmite cada modo está **fijo en
el firmware**: solo el Custom Mode permite cambiarlo.

| Modo | Canal | Notas | ¿Editable? |
|---|---|---|---|
| Drum | 1 | 36–99 | no |
| Key | 1 | 36–84 (C2–C6) | no |
| **User** | **3** | **36–99 + 100–107** | no |
| Custom | 1 por defecto | 36–99, note/CC/PC por pad | sí, 1–16 |
| Easy | — | modo audio/luces independiente | — |

**El User Mode es el que hay que usar.** Es el único modo en el que el
aparato acepta MIDI entrante para manejar sus LEDs.

Como Drum y Key están los dos en el canal 1 y con rangos de notas que se
superponen, Live no puede distinguirlos. Si querés tener una capa de batería
y una melódica armadas al mismo tiempo, configurá el **Custom Mode en el
canal 2** con el editor del fabricante y usá ese en vez del Drum Mode.

## 2. Mapa de notas de la grilla — no es lineal

Acá tropieza todo el mundo. La grilla 8×8 son **dos bloques de cuatro
columnas**:

- Las columnas 1–4 son las notas 36–67
- Las columnas 5–8 son las notas 68–99

```python
def nota_de(columna, fila):      # fila 0 = fila de arriba
    return 36 + 32 * (columna // 4) + (7 - fila) * 4 + (columna % 4)
```

El inverso:

```python
def pad_de(nota):                # devuelve (columna, fila), fila 0 = arriba
    d = nota - 36
    return (4 * (d // 32) + (d % 32) % 4,
            7 - (d % 32) // 4)
```

Las esquinas, para verificar cualquier implementación:

```
arriba-izq  64      arriba-der  99
abajo-izq   36      abajo-der   71
```

## 3. Botones laterales

Los ocho botones del borde derecho mandan **notas 100–107 en el canal 3**,
momentáneos (127 al presionar, 0 al soltar), de arriba hacia abajo:

| Nota | Serigrafía |
|---|---|
| 100 | Octave |
| 101 | Transpose |
| 102 | Velocity |
| 103 | Light |
| 104 | MMC |
| 105 | Stop |
| 106 | Play |
| 107 | Record |

La tabla de funciones del manual los marca como inactivos en User Mode, y en
cuanto a su función *serigrafiada* es cierto: Stop, Play y Record no manejan
el transporte. Pero sí transmiten notas en el canal 3, así que un script
puede mapearlos a lo que quiera.

**Tienen la paleta RGB completa**, igual que los pads. Al principio parecía
que solo hacían rojo, verde y blanco; eso eran los valores por defecto del
framework, no un límite del hardware.

Los botones de arriba (selectores de modo y flechas) **no mandan nada**.

## 4. Paleta de colores — es la del Launchpad

**El Z-1 replica la paleta RGB del Novation Launchpad, exacta.**

Verificado de dos formas independientes:

1. **Fotografiado sobre el hardware.** Barrido de las 127 velocities, una
   fila de 8 por foto, con un pad blanco de anclaje para corregir el balance
   de blancos de la cámara y una etiqueta binaria para que cada foto se
   identifique sola.
2. **Contra las tablas de Ableton.** El archivo `Launchpad_MK2/Colors.py` de
   Live 9.7 contiene `RGB_COLOR_TABLE`, con 128 pares velocity→RGB.
   Coincidió con la medición fotográfica en los 128 valores.

Consecuencias prácticas:

- La `CLIP_COLOR_TABLE` de Ableton mapea directo los 60 colores de clip de
  Live sobre este aparato. Usala, no escribas tu propio emparejador de
  colores cercanos.
- `SessionComponent.set_rgb_mode(CLIP_COLOR_TABLE, RGB_COLOR_TABLE)`
  funciona tal cual.
- Las constantes de color del Launchpad (`Rgb.GREEN` = 21, etc.) son válidas
  acá.

### Estructura de la paleta

- **0–3** — apagado, gris oscuro, gris, blanco
- **4–63** — 15 familias de tono, de 4 valores cada una:
  `[pálido, pleno, oscuro, tenue]`. Rojo 4–7, naranja 8–11, amarillo 12–15,
  lima 16–19, verdes 20–31, cyan 32–39, azul 40–47, violeta 48–51,
  magenta 52–55, rosa 56–59.
- **64–127** — colores sueltos, sin estructura. Este es el rango que
  realmente usa la paleta de clips de Live.

**La paleta de clips de Live solo usa las velocities 60–119.** Todo lo que
está fuera de ese rango queda libre para estados de interfaz y no puede
confundirse nunca con el color de un clip. Si estás diseñando feedback, ese
es el dato más útil de todo este documento.

Las familias de 4 valores entre 4 y 63 sirven para un esquema de "una
familia de color por canción, un tono por función". Pero tené en cuenta que
las variantes `oscuro` y `tenue` tienen muy poco brillo y son difíciles de
leer con luz de escenario.

## 5. Lo que el Z-1 no puede hacer

### No tiene parpadeo ni pulso

El Launchpad le pide a su hardware que parpadee o pulse mandando la nota por
otro canal MIDI (`BLINK_LED_CHANNEL = 1` y `PULSE_LED_CHANNEL = 2` en
`Launchpad_MK2/consts.py`). Por eso Ableton puede usar el mismo verde para
"clip verde detenido" y para "sonando": la distinción la da el movimiento,
no el tono.

**El Z-1 no lo implementa.** Se probaron los 16 canales MIDI
(`tools/z1_parpadeo.py`): solo el canal 3 enciende algo, y siempre fijo.

Consecuencia: o elegís colores de estado que no puedan chocar con los
colores de clip, o parpadeás por software. Este script hace las dos cosas:
colores distintos para sonando y grabando, y parpadeo por software para el
estado en cola.

### Los LEDs se apagan al cambiar de modo, en silencio

Si pasás el Z-1 a Drum, Key o Custom y volvés a User, todos los LEDs quedan
apagados. **El aparato no manda nada por MIDI cuando cambia de modo**, así
que un script no tiene forma de saber que debe repintar.

No hay manera de evitar un refresco manual. Ojo con un detalle: hay que
limpiar la caché de envío, porque el framework no reenvía un valor idéntico
al último que mandó.

```python
matriz.clear_send_cache()
for boton in botones_laterales:
    boton.clear_send_cache()
self.refresh_state()
```

### La velocity es fija en User Mode

El User Mode transmite velocity máxima sin importar la fuerza del golpe.
Sirve para lanzar clips, no sirve para tocar. Para eso usá Drum o Custom.

## 6. Alimentación

Declara 2.5 W. A 5 V son unos 500 mA, el presupuesto entero de un puerto USB
2.0. El aparato tiene una entrada USB-C de alimentación separada: **usala**,
sobre todo si compartís bus con una placa de audio bus-powered. Fue un
problema real en la máquina de desarrollo (MacBook Pro 2012 con un Mbox 2).

## 7. Editor del fabricante

El editor de Synido requiere **macOS 10.14 o superior**. No corre en
sistemas más viejos, lo cual importa si estás usando Live 9 sobre un macOS
antiguo. La configuración se escribe en el aparato, así que podés
configurarlo en una máquina nueva y usarlo en una vieja.

Los archivos de configuración del editor guardan los colores como **tripletes
RGB**, no como índices de velocity, lo que sugiere que el aparato podría
aceptar RGB por SysEx para configurar el Custom Mode. **No lo investigamos.**
Si el RGB por SysEx funcionara en tiempo real, eliminaría el límite de 128
colores. Buen primer aporte: capturar lo que manda el editor al hacer clic
en "Send to Hardware".

## 8. Cómo reproducir las mediciones

`tools/z1_filas.py` es el banco de medición. Enciende la fila de arriba con
8 velocities consecutivas y codifica el número de pasada en binario en la
fila de abajo, así cada foto se identifica sola y nada depende del orden de
captura.

```bash
pip3 install mido python-rtmidi
python3 tools/z1_filas.py plan                   # imprime las 16 pasadas
python3 tools/z1_filas.py ports
python3 tools/z1_filas.py fila 1 --port "TempoPAD"
```

Sacá las fotos con ISO bajo. Los centros de LED sobreexpuestos se queman a
blanco y destruyen el tono: eso arruinó el primer intento.
