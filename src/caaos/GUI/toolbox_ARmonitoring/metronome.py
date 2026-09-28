from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia
import os
import sys


"""
Respiratory metronome widget for guided inflate/deflate pacing.

This module provides two Qt widgets:

- :class:`LungBarWidget`:
  A custom-painted vertical bar used to represent lung inflation/deflation.
- :class:`RespiratoryMetronomeWidget`:
  A complete metronome UI with controls for total time, click frequency,
  sound volume, and optional click-sound file selection.

Behavioral sequence
-------------------
The timing logic follows this exact cycle:

    SOUND -> bar increases to maximum -> SOUND -> bar decreases to zero -> repeat

Where each SOUND occurs at a segment boundary.

Frequency semantics
-------------------
``frequency_hz`` is interpreted as "sounds per second" (click rate). Therefore:

- 0.5 Hz  => one sound every 2 seconds
- 1.0 Hz  => one sound every 1 second
- 2.0 Hz  => two sounds per second

Dependencies
------------
- PyQt5.QtCore
- PyQt5.QtGui
- PyQt5.QtWidgets
- PyQt5.QtMultimedia (for :class:`QSoundEffect`)

Notes
-----
- If no valid sound file is configured, the widget still runs visually.
- For best compatibility with ``QSoundEffect``, prefer WAV files.
"""

class LungBarWidget(QtWidgets.QWidget):
    """
    Visual breathing bar for inflation/deflation feedback (vertical orientation).

    The widget renders a vertical bar whose fill ratio is derived from
    two state variables:

    - ``phase`` (float in [0, 1]): progress inside the current segment.
    - ``ascending`` (bool): whether the current segment is inflation
      (increasing) or deflation (decreasing).

    During inflation, fill grows from bottom to top.
    During deflation, fill shrinks from top to bottom.
    """

    def __init__(self, parent=None):
        """
        Initialize the vertical breathing bar widget.

        :param parent: Optional parent widget.
        :type parent: QWidget or None
        """
        super().__init__(parent)
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        self._phase = 0.0          # 0.0 -> 1.0 within one segment
        self._ascending = True     # True: inflate, False: deflate

    def set_state(self, phase: float, ascending: bool):
        """
        Update visual state for the current breathing segment.

        :param phase:
            Segment progress in the interval [0.0, 1.0]. Values are clamped.
        :type phase: float
        :param ascending:
            ``True`` for inflation (bar grows upward), ``False`` for deflation
            (bar shrinks downward).
        :type ascending: bool
        """
        self._phase = max(0.0, min(1.0, phase))
        self._ascending = ascending
        self.update()

    def paintEvent(self, _event):
        """
        Paint the vertical breathing bar and directional text.

        This method draws:

        1. A rounded frame/background (full widget height).
        2. A gradient-filled region from bottom upward based on fill ratio.
        3. Centered status text ("Inflating" or "Deflating").

        :param _event: Qt paint event (unused directly).
        :type _event: QPaintEvent
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        frame = self.rect().adjusted(10, 10, -10, -10)

        # frame background
        painter.setPen(QtGui.QPen(QtGui.QColor(110, 110, 110), 1))
        painter.setBrush(QtGui.QColor(243, 243, 243))
        painter.drawRoundedRect(frame, 8, 8)

        # fill ratio: current phase if ascending, inverted if descending
        fill_ratio = self._phase if self._ascending else (1.0 - self._phase)

        # vertical fill: grows from bottom upward
        fill_h = int(frame.height() * fill_ratio)
        fill_rect = QtCore.QRect(
            frame.left(),
            frame.bottom() - fill_h,
            frame.width(),
            fill_h
        )

        grad = QtGui.QLinearGradient(fill_rect.bottomLeft(), fill_rect.topLeft())
        grad.setColorAt(0.0, QtGui.QColor(45, 145, 225))
        grad.setColorAt(1.0, QtGui.QColor(130, 205, 255))
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(grad))
        painter.drawRoundedRect(fill_rect, 8, 8)

        # text label
        txt = "Inspire" if self._ascending else "Expire"
        font = QtGui.QFont()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QtGui.QPen(QtGui.QColor(45, 45, 45)))
        painter.drawText(frame, QtCore.Qt.AlignCenter, txt)


class RespiratoryMetronomeWidget(QtWidgets.QWidget):
    """
    Standalone respiratory metronome widget with audio and animated vertical bar.

    Layout
    ------
    The widget uses a two-column layout:

    - **Left**: Vertical breathing bar (tall, narrow).
    - **Right**: All controls (duration, frequency, volume, sound file, progress, buttons).

    Features
    --------
    - Total runtime configuration (seconds).
    - Adjustable metronome frequency (Hz, interpreted as sounds/sec).
    - Adjustable audio volume (0-100%).
    - Optional click sound selection from file.
    - Progress/status display.
    - Inflate/deflate visual animation synchronized with click boundaries.

    Signals
    -------
    .. py:attribute:: started
       :type: pyqtSignal

       Emitted when the metronome starts.

    .. py:attribute:: stopped
       :type: pyqtSignal

       Emitted when the metronome stops (manual or internal).

    .. py:attribute:: finished
       :type: pyqtSignal

       Emitted when total configured runtime is reached.
    """

    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """
        Construct the respiratory metronome widget.

        Initializes:
        - runtime state variables,
        - animation and sound timers,
        - audio engine (:class:`QSoundEffect`),
        - UI controls and signal wiring.

        :param parent: Optional parent widget.
        :type parent: QWidget or None
        """
        super().__init__(parent)

        # runtime state
        self._running = False
        self._duration_ms = 30_000
        self._elapsed_ms = 0
        self._frequency_hz = 0.5          # sounds per second
        self._sound_interval_ms = int(1000 / self._frequency_hz)  # time between sounds
        self._segment_start_ms = 0        # elapsed time at last SOUND boundary
        self._ascending = True            # first segment: rise

        # timers
        self._tick_timer = QtCore.QTimer(self)
        self._tick_timer.setInterval(20)
        self._tick_timer.timeout.connect(self._on_tick)

        self._sound_timer = QtCore.QTimer(self)
        self._sound_timer.timeout.connect(self._on_sound_boundary)

        # sound
        self._sound = QtMultimedia.QSoundEffect(self)
        self._sound.setVolume(0.5)

        self._build_ui()
        self._wire_signals()
        self._apply_frequency()

    def _build_ui(self):
        """
        Build all UI controls and layout.

        Creates a two-column layout:
        - Left: :class:`LungBarWidget`
        - Right: Form controls, progress, and action buttons.
        """
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # === LEFT: Vertical breathing bar ===
        self.lung_bar = LungBarWidget()
        main_layout.addWidget(self.lung_bar, stretch=2)

        # === RIGHT: Controls ===
        right_layout = QtWidgets.QVBoxLayout()

        form = QtWidgets.QFormLayout()

        self.total_time_spin = QtWidgets.QSpinBox()
        self.total_time_spin.setRange(1, 24 * 3600)
        self.total_time_spin.setValue(30)
        self.total_time_spin.setSuffix(" s")
        form.addRow("Total time:", self.total_time_spin)

        self.freq_spin = QtWidgets.QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 4.0)
        self.freq_spin.setDecimals(2)
        self.freq_spin.setSingleStep(0.1)
        self.freq_spin.setValue(0.5)
        self.freq_spin.setSuffix(" Hz")
        form.addRow("Metronome frequency:", self.freq_spin)

        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        form.addRow("Volume:", self.volume_slider)

        sound_row = QtWidgets.QHBoxLayout()
        self.sound_edit = QtWidgets.QLineEdit()
        self.sound_edit.setPlaceholderText("Optional click .wav file")
        self.sound_btn = QtWidgets.QPushButton("Browse...")
        sound_row.addWidget(self.sound_edit)
        sound_row.addWidget(self.sound_btn)
        sound_container = QtWidgets.QWidget()
        sound_container.setLayout(sound_row)
        form.addRow("Click sound:", sound_container)

        right_layout.addLayout(form)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        right_layout.addWidget(self.progress)

        self.status = QtWidgets.QLabel("Stopped")
        right_layout.addWidget(self.status)

        buttons = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)
        right_layout.addLayout(buttons)

        right_layout.addStretch()

        main_layout.addLayout(right_layout, stretch=1)

    def _wire_signals(self):
        """
        Connect Qt signals from controls to widget slots/callbacks.

        Includes:
        - start/stop button actions,
        - control value-change handlers,
        - sound browsing/edit completion handlers.
        """
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

        self.total_time_spin.valueChanged.connect(self._on_total_time_changed)
        self.freq_spin.valueChanged.connect(self._on_frequency_changed)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

        self.sound_btn.clicked.connect(self._browse_sound_file)
        self.sound_edit.editingFinished.connect(self._on_sound_edit_finished)

    # ---------- public ----------
    def start(self):
        """
        Start metronome execution from initial phase.

        Start behavior:
        1. Reset elapsed/runtime state.
        2. Set first segment to inflation.
        3. Emit immediate SOUND at t=0.
        4. Start sound-boundary timer and animation tick timer.
        5. Emit :attr:`started`.
        """
        if self._running:
            return

        self._duration_ms = self.total_time_spin.value() * 1000
        self._elapsed_ms = 0
        self._segment_start_ms = 0
        self._ascending = True  # first segment must rise
        self._apply_frequency()

        self._running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setValue(0)

        # First SOUND at t=0, then start rising.
        self._play_click()
        self.lung_bar.set_state(0.0, True)
        self.status.setText("Running - remaining: {}s".format(self._duration_ms // 1000))

        self._sound_timer.start(self._sound_interval_ms)
        self._tick_timer.start()
        self.started.emit()

    def stop(self):
        """
        Stop metronome execution.

        Stops internal timers, updates button/status state,
        and emits :attr:`stopped`.
        """
        if not self._running:
            return
        self._tick_timer.stop()
        self._sound_timer.stop()
        self._running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status.setText("Stopped")
        self.stopped.emit()

    # ---------- internal ----------
    def _apply_frequency(self):
        """
        Recompute step interval from current frequency.

        ``_sound_interval_ms`` is the time between consecutive SOUND events and is
        derived from ``frequency_hz``:

        ``sound_interval_ms = 1000 / frequency_hz``

        A lower bound is applied to avoid unstable very-short intervals.
        """
        self._sound_interval_ms = max(50, int(1000 / max(0.1, self._frequency_hz)))
        self._sound_timer.setInterval(self._sound_interval_ms)

    def _on_tick(self):
        """
        Periodic animation/progress update callback.

        Called by ``_tick_timer``:
        - advances elapsed time,
        - checks for duration completion,
        - updates progress label/bar,
        - updates breathing bar interpolation.
        """
        if not self._running:
            return

        self._elapsed_ms += self._tick_timer.interval()
        if self._elapsed_ms >= self._duration_ms:
            self._elapsed_ms = self._duration_ms
            self._update_progress()
            self.stop()
            self.status.setText("Finished")
            self.finished.emit()
            return

        self._update_progress()
        self._update_bar()

    def _on_sound_boundary(self):
        """
        Handle SOUND boundary event.

        At each boundary:
        - play click sound,
        - reset segment origin time,
        - toggle direction (inflate <-> deflate).

        This enforces the sequence:
        SOUND -> rise -> SOUND -> fall -> SOUND -> ...
        """
        if not self._running:
            return

        # SOUND at boundary (max or min).
        self._play_click()

        # Reset phase origin for next segment interpolation.
        self._segment_start_ms = self._elapsed_ms

        # Toggle direction for next segment:
        # rise -> fall -> rise -> ...
        self._ascending = not self._ascending

    def _update_bar(self):
        """
        Interpolate bar phase inside current segment.

        Computes segment-local phase as:

        ``phase = (elapsed - segment_start) / sound_interval_ms``

        Then clamps phase to [0, 1] and updates :class:`LungBarWidget`.
        """
        dt = self._elapsed_ms - self._segment_start_ms
        phase = dt / float(max(1, self._sound_interval_ms))
        phase = max(0.0, min(1.0, phase))
        self.lung_bar.set_state(phase, self._ascending)

    def _update_progress(self):
        """
        Update progress bar and remaining-time text.

        Progress bar uses a normalized 0..1000 range.
        Status text displays integer remaining seconds.
        """
        ratio = self._elapsed_ms / float(max(1, self._duration_ms))
        self.progress.setValue(int(ratio * 1000))
        rem_s = max(0, (self._duration_ms - self._elapsed_ms) // 1000)
        self.status.setText("Running - remaining: {}s".format(rem_s))

    def _play_click(self):
        """
        Play click sound if a valid sound source is configured.

        If no source is set, this method is a no-op.
        """
        if self._sound.source().isEmpty():
            return
        self._sound.play()

    # ---------- ui callbacks ----------
    def _on_total_time_changed(self, sec):
        """
        Update target runtime from UI value.

        :param sec: Total runtime in seconds.
        :type sec: int
        """
        self._duration_ms = int(sec * 1000)

    def _on_frequency_changed(self, hz):
        """
        Update metronome frequency and internal interval.

        :param hz: Click rate (sounds per second).
        :type hz: float
        """
        self._frequency_hz = float(hz)
        self._apply_frequency()

    def _on_volume_changed(self, value):
        """
        Update click-sound volume.

        :param value: Slider value in the range [0, 100].
        :type value: int
        """
        self._sound.setVolume(float(value) / 100.0)

    def _browse_sound_file(self):
        """
        Open file dialog to select a click sound file.

        The selected path is copied to the sound-path line edit and loaded.
        """
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select metronome click sound",
            "",
            "WAV files (*.wav);;All files (*)",
        )
        if path:
            self.sound_edit.setText(path)
            self._set_sound(path)

    def _on_sound_edit_finished(self):
        """
        Load sound file from the manual path edit field.
        """
        self._set_sound(self.sound_edit.text().strip())

    def _set_sound(self, path):
        """
        Configure click-sound source path.

        If ``path`` exists as a file, it is loaded into ``QSoundEffect``.
        Otherwise, the sound source is cleared (silent operation).

        :param path: Local file path to click sound.
        :type path: str
        """
        if path and os.path.isfile(path):
            self._sound.setSource(QtCore.QUrl.fromLocalFile(path))
        else:
            self._sound.setSource(QtCore.QUrl())


if __name__ == "__main__":
    """
    Local demo runner for the respiratory metronome widget.

    Run this file directly to test the widget in isolation.
    """
    app = QtWidgets.QApplication(sys.argv)
    w = RespiratoryMetronomeWidget()
    w.setWindowTitle("Respiratory Metronome")
    w.resize(700, 400)
    w.show()
    sys.exit(app.exec_())