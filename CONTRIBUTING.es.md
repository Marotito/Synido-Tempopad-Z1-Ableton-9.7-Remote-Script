# Cómo colaborar

*[English version](CONTRIBUTING.md)*

Esto empezó como un proyecto personal para volver usable en Live un clon
barato de Launchpad, y funciona lo suficientemente bien como para tocar en
vivo. Es público porque los hallazgos sobre el hardware valen la pena
compartirlos y porque queda bastante por construir.

Issues, ideas y PRs son todos bienvenidos, incluido "esto no me funciona en
mi setup", que también es información útil.

## Antes de escribir código

Leé [docs/ARCHITECTURE.es.md](docs/ARCHITECTURE.es.md), sobre todo la
sección de trampas del framework. La mayoría costó horas de encontrar y no
están documentadas en ningún otro lado.

Dos convenciones que se ganaron su lugar:

- **Escribí Python que parsee como 2.7 y como 3.** Live 9 corre 2.7, pero
  evitando `except X, e` y `print` como sentencia podés verificar la
  sintaxis con python3 antes de desplegar. Cada despliegue cuesta reiniciar
  Live; atrapar los errores de sintaxis localmente vale esa pequeña
  restricción.
- **Leé el método del framework antes de llamarlo.** Los fuentes del
  `_Framework` decompilan sin problemas con `uncompyle6`. Las aserciones de
  ahí adentro son estrictas y fallan de formas que dejan el aparato a medio
  configurar.

## Pruebas

No hay un banco de pruebas para una control surface en vivo, pero se llega
bastante lejos decompilando el `_Framework` y simulando lo que haga falta.
El parpadeo por software se validó contra el `Task.py` real de Ableton con
un Live simulado, antes de tocar el hardware.

Cuando reportes un bug, incluí el `Log.txt`:

- macOS: `~/Library/Preferences/Ableton/Live 9.x/Log.txt`
- Windows: `%APPDATA%\Ableton\Live 9.x\Preferences\Log.txt`

O `./tools/deploy.sh log` en macOS.

## Hoja de ruta

### Zoom de sesión
`SessionZoomingComponent` muestra el set completo como bloques de 8×8: cada
pad es una región a la que saltás. Para un set organizado como bloques de
canciones con código de color, eso es directamente un selector de canciones.
Es lo que mejor relación valor/esfuerzo tiene de todo lo que falta.

### Stop por pista
`set_stop_track_clip_buttons` en una capa de shift. El Launchpad recorta una
fila de la matriz principal con `submatrix[:, 4:5]`; el mismo truco aplica.

### Modo mixer
`MixerComponent` da mute, solo y arm sin una línea de código propio. Ojo con
que `set_send_controls` espera controles **continuos**: llama a `connect_to`
sobre un parámetro, así que los sends no se pueden manejar desde pads sin
escribir código de LOM a mano.

### Port a Live 10 y 11
La API del `_Framework` cambió. Alguien con Live 10 o superior tendría que
verificar los mismos contratos de métodos documentados en ARCHITECTURE.

### SysEx y RGB directo
El editor del fabricante guarda los colores como tripletes RGB, lo que
sugiere que el aparato podría aceptar RGB por SysEx. Si eso funciona en
tiempo real, elimina el límite de 128 colores. Capturá lo que manda el
editor al hacer clic en "Send to Hardware" con MIDI Monitor: ese es todo el
experimento.

### Otros clones de Launchpad
Si tu aparato también resulta usar la paleta del Launchpad, la mayor parte
de esto es reutilizable: cambiás el mapa de notas y el canal. Los reportes
desde otro hardware son muy bienvenidos; `tools/z1_filas.py` y
`tools/z1_parpadeo.py` caracterizan un aparato nuevo en una tarde.

## Qué no va a hacer este proyecto

- Publicar un fork de los scripts de fábrica de Ableton. Se los referencia,
  no se los copia.
- Agregar funciones que necesiten capacidades de hardware que el Z-1 no
  tiene. Lo probamos: no parpadea. Trabajemos con eso.
