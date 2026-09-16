# -*- coding: utf-8 -*-
# ============================================================
#  Z1_Grid  -  FASE 4
#  Synido TempoPAD Z-1  ->  Ableton Live 9.7
#
#  MIGRADO a Layer + ModesComponent, el mecanismo nativo de capas.
#
#  Por que: las capas dejan de asignarse a mano. Un Layer es un
#  recurso; cuando el modo habilita su componente, el Layer agarra
#  sus controles solo, y al deshabilitarlo los suelta y vuelven al
#  duenio anterior. Eso escala a N capas -mixer, segundo shift- sin
#  que el codigo crezca.
#
#  REGLA DEL FRAMEWORK (ControlSurfaceComponent):
#      assert layer is None or not is_enabled
#  Todo componente que recibe un layer se crea DESHABILITADO.
#  Lo habilita el modo, y ahi el layer agarra sus controles.
#
#  MODOS
#    'sesion'  : grilla 8x8 de clips
#    'escenas' : columna 1 = escenas; el resto lo toma un
#                BackgroundComponent que lo apaga y evita que esas
#                notas se filtren a la pista MIDI
#
#  Z-1 en USER MODE (canal MIDI 3).
# ============================================================

from _Framework.ControlSurface import ControlSurface
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.SessionComponent import SessionComponent
from _Framework.BackgroundComponent import BackgroundComponent
from _Framework.InputControlElement import MIDI_NOTE_TYPE
from _Framework.Layer import Layer
from _Framework.ModesComponent import ModesComponent, AddLayerMode
from _Framework import Task

import paleta

CANAL = 2
ANCHO = 8
ALTO = 8

NOTA_REFRESCO      = 100   # Octave
NOTA_ESCENA_ARRIBA = 101   # Transpose
NOTA_ESCENA_ABAJO  = 102   # Velocity
NOTA_PISTA_IZQ     = 103   # Light
NOTA_PISTA_DER     = 104   # MMC
NOTA_STOP_TODO     = 105   # Stop
NOTA_ESCENA_SEL    = 106   # Play   (libre)
NOTA_SHIFT         = 107   # Record

# Colores de estado. Elegidos entre las velocities que la paleta de
# clips de Live NO usa (usa solo 60..119), asi un clip detenido nunca
# puede parecerse a uno sonando.
COLOR_SONANDO        = 53    # magenta pleno
COLOR_EN_COLA        = 13    # amarillo
COLOR_GRABANDO       = 56    # rosa fuerte
COLOR_COLA_GRABACION = 8     # naranja palido

COLOR_SHIFT_ON  = 53
COLOR_SHIFT_OFF = paleta.GRIS_MUY_OSCURO

# Parpadeo del estado EN COLA. El Z-1 no lo hace por hardware
# (probados los 16 canales: solo el 3 enciende, siempre fijo).
PARPADEO = True
PERIODO_PARPADEO = 0.25
DIAG = False


def nota_de(columna, fila):
    """fila 0 = fila de arriba"""
    return 36 + 32 * (columna // 4) + (7 - fila) * 4 + (columna % 4)


class Z1_Grid(ControlSurface):

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message('=========== Z1_Grid FASE 4 (Layer + Modes) ===========')
        self._shift = False
        self._fase = True
        self._parpadeando = False
        try:
            with self.component_guard():
                self._crear_controles()
                self._crear_sesion()
                self._crear_fondo()
                self._crear_modos()
            self._actualizar_led_shift()
            if PARPADEO:
                self._arrancar_parpadeo()
            self.log_message('Z1_Grid: listo. Z-1 en USER MODE.')
        except Exception as e:
            self.log_message('Z1_Grid: FALLO EL ARRANQUE -> ' + str(e))
            import traceback
            for linea in traceback.format_exc().split('\n'):
                self.log_message('    ' + linea)
        self.log_message('======================================================')

    # ---------------- controles ----------------
    def _crear_controles(self):
        filas = []
        for fila in range(ALTO):
            botones = []
            for col in range(ANCHO):
                b = ButtonElement(True, MIDI_NOTE_TYPE, CANAL,
                                  nota_de(col, fila))
                b.name = 'Pad_%d_%d' % (col, fila)
                botones.append(b)
            filas.append(botones)
        self._filas = filas
        self._matriz = ButtonMatrixElement(rows=filas, name='Grilla')
        # set_scene_launch_buttons EXIGE una matriz de ancho = num_scenes
        # y alto = 1. La disposicion fisica es una columna, pero la forma
        # LOGICA tiene que ser una fila de 8. No es lo mismo.
        columna_0 = [filas[f][0] for f in range(ALTO)]
        self._col_escenas = ButtonMatrixElement(rows=[columna_0],
                                                name='Escenas')
        # submatrix[columnas, filas] -> columnas 2..8, todas las filas
        self._resto = self._matriz.submatrix[1:, :]

        self._b_refresco = self._boton(NOTA_REFRESCO, 'Refresco')
        self._b_esc_arr = self._boton(NOTA_ESCENA_ARRIBA, 'Escena_Arriba')
        self._b_esc_aba = self._boton(NOTA_ESCENA_ABAJO, 'Escena_Abajo')
        self._b_pis_izq = self._boton(NOTA_PISTA_IZQ, 'Pista_Izq')
        self._b_pis_der = self._boton(NOTA_PISTA_DER, 'Pista_Der')
        self._b_stop = self._boton(NOTA_STOP_TODO, 'Stop_Todo')
        self._b_shift = self._boton(NOTA_SHIFT, 'Shift')
        self._laterales = [self._b_refresco, self._b_esc_arr,
                           self._b_esc_aba, self._b_pis_izq,
                           self._b_pis_der, self._b_stop, self._b_shift]
        self._b_refresco.add_value_listener(self._al_refrescar)
        self._b_shift.add_value_listener(self._al_shift)

    def _boton(self, nota, nombre):
        b = ButtonElement(True, MIDI_NOTE_TYPE, CANAL, nota)
        b.name = nombre
        return b

    # ---------------- sesion ----------------
    def _crear_sesion(self):
        # is_enabled=False obligatorio: lleva layer. Lo habilita el modo.
        self._sesion = SessionComponent(
            ANCHO, ALTO, name='Sesion', is_enabled=False,
            layer=Layer(track_bank_left_button=self._b_pis_izq,
                        track_bank_right_button=self._b_pis_der,
                        scene_bank_up_button=self._b_esc_arr,
                        scene_bank_down_button=self._b_esc_aba,
                        stop_all_clips_button=self._b_stop))
        self._sesion.set_offsets(0, 0)
        # modo RGB nativo: color real de clips y escenas, con listeners
        # propios del framework. OJO: set_clip_palette deja
        # _stopped_value en None, y ese None es lo que activa la rama
        # del color del clip. Los valores de estado van DESPUES.
        self._sesion.set_rgb_mode(paleta.CLIP, paleta.RGB_TABLA)
        for f in range(ALTO):
            escena = self._sesion.scene(f)
            escena.name = 'Escena_%d' % f
            escena.set_triggered_value(COLOR_EN_COLA)
            for c in range(ANCHO):
                slot = escena.clip_slot(c)
                slot.name = 'Slot_%d_%d' % (c, f)
                slot.set_started_value(COLOR_SONANDO)
                slot.set_recording_value(COLOR_GRABANDO)
                slot.set_triggered_to_play_value(COLOR_EN_COLA)
                slot.set_triggered_to_record_value(COLOR_COLA_GRABACION)
        self._sesion.set_show_highlight(True)

    def _crear_fondo(self):
        # Apaga los pads que la capa activa no usa y evita que esas
        # notas se cuelen como MIDI a la pista.
        self._fondo = BackgroundComponent(
            name='Fondo', is_enabled=False,
            layer=Layer(grilla=self._resto))

    # ---------------- modos ----------------
    def _crear_modos(self):
        self._modos = ModesComponent(name='Modos', is_root=True)
        self._modos.add_mode('sesion', [
            self._sesion,
            AddLayerMode(self._sesion,
                         Layer(clip_launch_buttons=self._matriz))])
        self._modos.add_mode('escenas', [
            self._sesion,
            AddLayerMode(self._sesion,
                         Layer(scene_launch_buttons=self._col_escenas)),
            self._fondo])
        self._modos.selected_mode = 'sesion'

    # ---------------- shift ----------------
    def _al_shift(self, value):
        # Enganche. El boton lo manejamos nosotros y solo cambiamos de
        # modo: el resto -agarrar y soltar controles- lo hace el Layer.
        if value == 0:
            return
        self._shift = not self._shift
        try:
            self._modos.selected_mode = 'escenas' if self._shift else 'sesion'
            self._actualizar_led_shift()
            self.log_message('Z1_Grid: modo %s' % self._modos.selected_mode)
        except Exception as e:
            self.log_message('Z1_Grid: fallo el cambio de modo -> ' + str(e))
            import traceback
            for linea in traceback.format_exc().split('\n'):
                self.log_message('    ' + linea)
            # Un cambio de modo a medias deja controles sueltos y el
            # aparato erratico. Volvemos a un estado conocido.
            try:
                self._shift = False
                self._modos.selected_mode = 'sesion'
                self._actualizar_led_shift()
                self.log_message('Z1_Grid: recuperado a modo sesion')
            except Exception:
                self.log_message('Z1_Grid: NO se pudo recuperar. '
                                 'Reinicia Live.')

    def _actualizar_led_shift(self):
        self._b_shift.send_value(
            COLOR_SHIFT_ON if self._shift else COLOR_SHIFT_OFF, force=True)

    # ---------------- parpadeo del estado EN COLA ----------------
    def _arrancar_parpadeo(self):
        self._tasks.add(
            Task.repeat(
                Task.sequence(Task.wait(PERIODO_PARPADEO),
                              Task.run(self._alternar_fase))))
        self.log_message('Z1_Grid: parpadeo activo (%.2f s)' % PERIODO_PARPADEO)

    def _hay_encolado(self):
        try:
            cancion = self.song()
            for pista in cancion.tracks:
                if pista.fired_slot_index != -1:
                    return True
            for escena in cancion.scenes:
                if escena.is_triggered:
                    return True
        except Exception:
            return False
        return False

    def _pintar_encolado(self, encendido):
        color = COLOR_EN_COLA if encendido else paleta.APAGADO
        color_rec = COLOR_COLA_GRABACION if encendido else paleta.APAGADO
        for f in range(ALTO):
            escena = self._sesion.scene(f)
            escena.set_triggered_value(color)
            for c in range(ANCHO):
                slot = escena.clip_slot(c)
                slot.set_triggered_to_play_value(color)
                slot.set_triggered_to_record_value(color_rec)
        self._repintar_disparados()

    def _repintar_disparados(self):
        """SessionComponent.update() no cascadea hasta los ClipSlotComponent:
        cambiar el valor no alcanza, hay que pedir el redibujado.
        Repintamos solo las columnas y escenas con algo disparado."""
        try:
            cancion = self.song()
            try:
                pistas = list(cancion.visible_tracks)
            except Exception:
                pistas = list(cancion.tracks)
            try:
                t0 = self._sesion.track_offset()
                s0 = self._sesion.scene_offset()
            except Exception:
                t0, s0 = 0, 0
            for i, pista in enumerate(pistas):
                if pista.fired_slot_index == -1:
                    continue
                col = i - t0
                if 0 <= col < ANCHO:
                    for f in range(ALTO):
                        self._sesion.scene(f).clip_slot(col).update()
            for i, escena in enumerate(cancion.scenes):
                if not escena.is_triggered:
                    continue
                fila = i - s0
                if 0 <= fila < ALTO:
                    self._sesion.scene(fila).update()
        except Exception as e:
            self.log_message('Z1_Grid: fallo el repintado -> ' + str(e))

    def _alternar_fase(self):
        try:
            hay = self._hay_encolado()
            if not hay:
                if self._parpadeando:
                    self._parpadeando = False
                    self._fase = True
                    self._pintar_encolado(True)
                return
            self._parpadeando = True
            self._fase = not self._fase
            self._pintar_encolado(self._fase)
            if DIAG:
                self.log_message('Z1_Grid: [diag] fase %s'
                                 % ('ON' if self._fase else 'OFF'))
        except Exception as e:
            self.log_message('Z1_Grid: fallo el parpadeo -> ' + str(e))

    # ---------------- refresco ----------------
    def _al_refrescar(self, value):
        # El Z-1 apaga sus LEDs al cambiar de modo en el hardware y no
        # avisa nada, asi que el redibujado lo pide el usuario.
        if value == 0:
            return
        try:
            self._matriz.clear_send_cache()
            for b in self._laterales:
                b.clear_send_cache()
            self.refresh_state()
            self._actualizar_led_shift()
            self.log_message('Z1_Grid: refresco desde el hardware')
        except Exception as e:
            self.log_message('Z1_Grid: fallo el refresco -> ' + str(e))

    # ---------------- limpieza ----------------
    def disconnect(self):
        for boton, cb in ((self._b_refresco, self._al_refrescar),
                          (self._b_shift, self._al_shift)):
            try:
                if boton.value_has_listener(cb):
                    boton.remove_value_listener(cb)
            except Exception:
                pass
        self.log_message('Z1_Grid: disconnect')
        ControlSurface.disconnect(self)
