# Z1_Grid — script de control surface del Synido TempoPAD Z-1 para Ableton Live 9

*[English version](README.md)*

Un MIDI Remote Script que convierte al **Synido TempoPAD Z-1** en un
lanzador de clips real para la Session View de Ableton Live 9, con los
colores reales de los clips, lanzamiento de escenas y una capa de shift.

**Estado: MVP funcionando.** Estable para usar a diario en Live 9.7 sobre
macOS. Todo lo que está documentado acá fue probado en el hardware, no es
teoría.

El Z-1 viene sin ninguna integración con Live: el fabricante solo entrega un
`UserConfiguration.txt` de fábrica que mapea tres botones de transporte.
Este script reemplaza eso por una control surface de verdad.

---

## Si llegaste buscando información del Z-1

Aunque nunca uses el script, [docs/HARDWARE.es.md](docs/HARDWARE.es.md) es
probablemente lo que viniste a buscar. En resumen:

- **El Z-1 usa la paleta de colores del Novation Launchpad, exacta.**
  Verificado de dos formas independientes. Las tablas del propio
  `Launchpad_MK2/Colors.py` de Ableton funcionan sin modificar.
- **El User Mode es el canal MIDI 3.** Los pads son las notas 36–99 y los
  botones laterales 100–107.
- **La grilla 8×8 no está numerada de forma lineal.** Las columnas 1–4
  arrancan en 36 y las columnas 5–8 en 68. La fórmula está en la doc.
- **No tiene parpadeo ni pulso.** Probamos los 16 canales MIDI: solo el
  canal 3 enciende, y siempre fijo. El truco del Launchpad de pedir el
  parpadeo por canal no funciona acá.
- **El aparato apaga sus LEDs al cambiar de modo por hardware, y no avisa
  nada por MIDI.** Cualquier script necesita un botón de refresco manual.

---

## Qué hace

- **Grilla 8×8 de clips** con los colores reales de Live, usando las tablas
  oficiales `CLIP_COLOR_TABLE` y `RGB_COLOR_TABLE` de Ableton. Los 60
  colores de clip de Live caen en 60 colores de pad distintos, sin
  colisiones.
- **Estados de reproducción legibles.** Sonando, en cola y grabando usan
  velocities fuera del rango que ocupa la paleta de clips de Live (60–119),
  así que un clip detenido nunca puede parecerse a uno sonando.
- **Parpadeo por software del estado "en cola"**, porque el hardware no
  puede hacerlo. No cuesta nada en reposo: solo repinta las columnas que
  realmente tienen un clip encolado.
- **Capa de shift** (botón Record, con enganche): la columna 1 lanza escenas
  con su color real, y el resto de la grilla lo apaga un
  `BackgroundComponent`, que además evita que esas notas se filtren a la
  pista MIDI armada.
- **Navegación de pistas y escenas** en los botones laterales, activa en
  ambas capas, con el recuadro de sesión de Live siguiendo el movimiento.
- **Refresco manual** (botón Octave) para cuando volvés al User Mode desde
  los modos Drum, Key o Custom.

## Requisitos

- Ableton Live 9.2 o superior (desarrollado y probado en 9.7)
- Synido TempoPAD Z-1
- macOS o Windows

## Instalación

Live 9 **no** soporta remote scripts en la User Library: eso recién llegó en
Live 10.1.13. El script tiene que ir adentro del bundle de la aplicación.

```
<Live>/Contents/App-Resources/MIDI Remote Scripts/Z1_Grid/
```

En macOS, `tools/deploy.sh` se encarga de todo, incluido el backup de los
scripts de fábrica y el borrado de los `.pyc` viejos. Corrélo desde la
máquina donde corre Live.

```bash
chmod +x tools/deploy.sh
./tools/deploy.sh          # desplegar
./tools/deploy.sh log      # seguir el Log.txt de Live
```

Los backups van a `~/Z1_Grid_backups` por defecto. Se cambia con
`--backup /alguna/ruta` o con la variable de entorno `Z1_BACKUP_DIR`.

Después, en Live: **Preferences → MIDI → Control Surface → Z1_Grid**, con el
Z-1 como Input y como Output. Poné el aparato en **User Mode**.

> Hacé backup de la carpeta `MIDI Remote Scripts` original antes de tocar
> nada. Si pisás un script de fábrica vas a tener que reinstalar Live para
> recuperarlo. `deploy.sh` lo hace por vos.

## Distribución de controles

```
        ┌───────────────────────────────┐
        │                               │  ← Octave     refresco
        │                               │  ← Transpose  escenas arriba
        │       grilla 8 × 8 de clips   │  ← Velocity   escenas abajo
        │                               │  ← Light      pistas izquierda
        │  col 1 = escenas con Shift    │  ← MMC        pistas derecha
        │                               │  ← Stop       detener todo
        │                               │  ← Play       (libre)
        │                               │  ← Record     SHIFT (enganche)
        └───────────────────────────────┘
```

| Estado | Velocity | Color |
|---|---|---|
| Clip detenido | del clip | color real del clip en Live |
| Clip sonando | 53 | magenta |
| Clip en cola | 13 | amarillo, parpadeando |
| Grabando | 56 | rosa fuerte |
| En cola para grabar | 8 | naranja pálido |
| Slot vacío | 0 | apagado |

Los colores de estado están elegidos a propósito fuera del rango 60–119, que
es el que ocupa la paleta de clips de Live. Por eso no pueden confundirse
nunca con el color propio de un clip. Si los cambiás, mantenelos fuera de
ese rango.

## Limitaciones conocidas

- **El hardware no parpadea.** El parpadeo del estado "en cola" lo hace una
  `Task` del framework. Es barato, pero no es gratis.
- **Hace falta refrescar a mano después de cambiar de modo en el aparato.**
  El Z-1 no informa los cambios de modo por MIDI, así que el script no puede
  saber que tiene que repintar.
- **Un solo botón por función lateral.** Hay 8 botones laterales y 7 ya
  están ocupados.
- **Por ahora solo Live 9.** La API del `_Framework` cambió en Live 10 y 11.
  Los ports son bienvenidos.

## Qué falta

Está todo en [CONTRIBUTING.es.md](CONTRIBUTING.es.md). En resumen:

- Zoom de sesión (vista del set completo como selector de canciones)
- Stop por pista en una capa de shift
- Modo mixer (mute, solo, arm)
- Port a Live 10 y 11

## Documentación

- [docs/HARDWARE.es.md](docs/HARDWARE.es.md) — todo lo que medimos del Z-1:
  mapa de notas, paleta, canales, y lo que no puede hacer
- [docs/ARCHITECTURE.es.md](docs/ARCHITECTURE.es.md) — cómo está armado el
  script y las trampas del framework que nos costaron tiempo
- [CONTRIBUTING.es.md](CONTRIBUTING.es.md) — hoja de ruta y cómo colaborar

## Herramientas

En `tools/` están los scripts de medición que usamos para caracterizar el
hardware. Corren fuera de Live y necesitan `mido` y `python-rtmidi`. Los
incluimos porque son la forma en que se produjeron los hallazgos, y porque
sirven para cualquier otro clon de Launchpad:

- `z1_filas.py` — barrido de las 127 velocities, una fila por foto, con
  etiqueta binaria para que cada foto se identifique sola
- `z1_parpadeo.py` — sondeo de los 16 canales MIDI buscando parpadeo o pulso
- `z1_colores.py` — barrido anterior en damero (superado, queda de referencia)

## Créditos

Proyecto concebido y dirigido por **Marote**, que hizo todas las pruebas y
mediciones sobre el hardware, decompiló el `_Framework` de Live y los
scripts de fábrica del Launchpad como referencia, tomó las decisiones de
diseño (distribución de canales, modelo de shift, esquema de colores) y
encontró varios bugs durante las pruebas.

Código y análisis técnico por **Claude** (Anthropic), trabajando a partir de
esas mediciones y decisiones.

Las tablas de color salen del propio `Launchpad_MK2/Colors.py` de Ableton,
que resultó aplicable a este aparato sin modificación.

## Licencia

MIT. Ver [LICENSE](LICENSE).

Sin relación con Synido, Ableton ni Novation.
