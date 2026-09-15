# Arquitectura

*[English version](ARCHITECTURE.md)*

Cómo está armado el script y, más útil todavía, las trampas del `_Framework`
que nos costaron tiempo. Todas se descubrieron a los golpes.

---

## Archivos

```
Z1_Grid/
  __init__.py     punto de entrada que busca Live (create_instance)
  Z1_Grid.py      la control surface
  paleta.py       tablas de color y helpers
```

`paleta.py` contiene las tablas `RGB_COLOR_TABLE` y `CLIP_COLOR_TABLE` de
Ableton (extraídas de `Launchpad_MK2/Colors.py`), más las familias de tono y
un helper `velocity_de_clip()` con emparejamiento por color cercano para
clips con color personalizado.

## Distribución de componentes

```
ControlSurface
├── ButtonMatrixElement  8×8      todos los pads, canal 3, notas 36–99
│     ├── matriz escenas 8×1      columna 1, rearmada como FILA (ver abajo)
│     └── submatrix[1:, :] 7×8    el resto, para el BackgroundComponent
├── 7 × ButtonElement               botones laterales, notas 100–107
├── SessionComponent (is_enabled=False, layer=navegación)
├── BackgroundComponent (is_enabled=False, layer=resto de la grilla)
└── ModesComponent
      ├── 'sesion'   → SessionComponent + clip_launch_buttons
      └── 'escenas'  → SessionComponent + scene_launch_buttons + Background
```

El cambio de modo lo maneja `ModesComponent`. El enganche del botón de shift
es nuestro; todo lo que viene después —agarrar y soltar controles— lo hace
el sistema de recursos `Layer` del framework. Agregar una capa de mixer más
adelante es sumar una llamada a `add_mode`, no tocar el código existente.

---

## Trampas del framework

Estas son las que nos mordieron de verdad. Si estás escribiendo un remote
script para Live 9, esta sección puede ser lo más útil del repo.

### `set_stopped_value()` desactiva el modo RGB en silencio

```python
def set_clip_palette(self, palette):
    self._stopped_value = None       # ← ese None es lo que activa el color
    self._clip_palette = palette

def set_stopped_value(self, value):
    self._stopped_value = value
    self._clip_palette = []          # ← borra la paleta
```

`_feedback_value()` cae en la rama del color del clip **solo** cuando
`_stopped_value` es `None`. Entonces:

- Llamá a `set_rgb_mode()` **primero**
- Asigná `set_started_value`, `set_recording_value` y `set_triggered_*`
  **después**: son campos separados y no molestan
- **Nunca** llames a `set_stopped_value()` con el modo RGB activo

No hay error ni advertencia: los clips simplemente dejan de mostrar su color.

### `SessionComponent.update()` no cascadea hasta los clip slots

Cambiar un valor de un `ClipSlotComponent` y llamar a `session.update()`
**no** repinta los pads. Hay que llamar a `update()` sobre los propios clip
slot components.

Por eso el parpadeo por software repinta slot por slot, y por eso toca solo
las columnas que tienen algo encolado en vez de los 64.

### `set_scene_launch_buttons` quiere una fila, no una columna

```python
assert not buttons or buttons.width() == self._num_scenes and buttons.height() == 1
```

Los botones de lanzamiento de escena tienen que ser una matriz de **8 de
ancho por 1 de alto**, sin importar cómo estén dispuestos físicamente.
Nuestra columna de escenas es vertical en el aparato, pero la matriz hay que
armarla como una sola fila:

```python
columna_0 = [filas[f][0] for f in range(8)]
matriz_escenas = ButtonMatrixElement(rows=[columna_0])
```

El Launchpad hace lo mismo con sus botones laterales, que también son
físicamente una columna. Pasar `submatrix[0:1, :]` da una matriz de 1×8 y no
pasa la aserción. Y como falla *durante* un cambio de modo, deja los
controles asignados a medias y el aparato con comportamiento errático.
Envolvé los cambios de modo en try/except y volvé a un modo conocido.

### Los componentes con layer tienen que arrancar deshabilitados

```python
assert layer is None or not is_enabled
```

Cualquier componente que se construya con `layer=` tiene que llevar
`is_enabled=False`. El modo lo habilita, y ahí `_internal_on_enabled_changed`
agarra el layer. Ese es todo el mecanismo: no hay asignación manual de
controles en ninguna parte.

### `send_value` no reenvía un valor idéntico

Usá `force=True` cuando necesites reenviar (por ejemplo después de un cambio
de modo en el hardware), o llamá antes a `clear_send_cache()`.

### `set_light()` con un entero no hace lo que parece

`ButtonElement.set_light(value)` trata su argumento como el **nombre de un
color de skin**, lo busca, y ante `SkinColorMissingError` cae en un simple
encendido/apagado. Como este script no usa skin, los enteros tienen que ir
por `send_value()`. El framework lo hace bien internamente:

```python
if in_range(value_to_send, 0, 128):
    button.send_value(value_to_send)
else:
    button.set_light(value_to_send)
```

### Los imports opcionales no pueden tumbar el script

Una versión temprana importaba un módulo de diagnóstico a nivel de módulo.
Cuando ese archivo faltó en un deploy, el script entero falló al cargar, y
el síntoma fue "no pasa absolutamente nada", que no apunta a ningún lado.
Protegé los imports opcionales:

```python
try:
    import contratos
except ImportError:
    contratos = None
```

---

## Parpadeo por software

El Z-1 no puede parpadear por hardware, así que el estado "en cola" parpadea
con una `Task` del framework. Live llama a `update_display()` cada 100 ms y
ahí tickean las tareas, así que 100 ms es el grano más fino disponible.

```python
self._tasks.add(
    Task.repeat(
        Task.sequence(Task.wait(0.25),
                      Task.run(self._alternar_fase))))
```

Control de costo:

- Antes de repintar, se consulta `track.fired_slot_index` y
  `scene.is_triggered`. Si no hay nada encolado, sale de inmediato. El costo
  en reposo es un chequeo barato por tick.
- Cuando sí hay algo encolado, repinta solo las columnas que tienen el clip
  en cola. Son 8 actualizaciones por fase, no 64.
- Cuando la cola se vacía, deja el color **encendido**, no apagado.

Medido: sin cambio observable de CPU en una MacBook Pro 2012 i5.

---

## Enfoque de testing

Los remote scripts de Live no se pueden testear directamente, pero los
módulos del `_Framework` se pueden decompilar (`uncompyle6`) y las partes
que importan se pueden simular. La lógica del parpadeo se validó contra el
`Task.py` **real** de Ableton con un Live simulado, antes de llegar al
hardware.

Dos cosas que vale la pena copiar:

- **Escribí en sintaxis válida en Python 2.7 y 3.** Live 9 corre 2.7, pero
  si evitás `except X, e` y compañía podés verificar la sintaxis con python3
  en cualquier máquina. Eso atrapa toda una clase de errores que si no
  descubrís recién al desplegar.
- **Verificá el contrato de cada método antes de escribir contra él.** Casi
  todos los bugs de este proyecto salieron de suponer qué hacía un método
  del framework en vez de leerlo. Las aserciones que nos rompieron estaban a
  la vista en fuentes que ya teníamos.

---

## Despliegue

Live 9 no soporta remote scripts en la User Library (recién desde 10.1.13),
así que el script vive adentro del bundle de la aplicación y se pierde al
reinstalar. Mantené el fuente bajo control de versiones en otro lado y
tratá al bundle como destino de despliegue. `tools/deploy.sh` hace eso, más
un backup de los scripts de fábrica estampado con la versión y el borrado de
los `.pyc` viejos: Live compila al arrancar, y un `.pyc` viejo significa
depurar código que ya no existe.
