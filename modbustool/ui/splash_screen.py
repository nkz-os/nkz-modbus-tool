"""Animated splash screen with particle effects, logos, and progress bar."""

import math
import random
import os

from PyQt6.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import (
    QPainter, QColor, QPixmap, QPainterPath, QLinearGradient,
    QFont, QFontMetrics, QRadialGradient, QPen,
)
from PyQt6.QtSvg import QSvgRenderer


class Particle:
    """A single electric particle."""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, -0.5)
        self.life = 1.0
        self.decay = random.uniform(0.01, 0.03)
        self.size = random.uniform(1.5, 4.0)
        self.trail = []

    def update(self):
        self.trail.append((self.x, self.y, self.life))
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.02  # slight gravity
        self.vx *= 0.99
        self.life -= self.decay
        return self.life > 0


class ElectricArc:
    """A lightning-like arc between two points."""

    def __init__(self, x1, y1, x2, y2, color):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color
        self.life = 1.0
        self.segments = self._generate_segments()

    def _generate_segments(self):
        segments = [(self.x1, self.y1)]
        steps = random.randint(5, 10)
        for i in range(1, steps):
            t = i / steps
            mx = self.x1 + (self.x2 - self.x1) * t + random.uniform(-15, 15)
            my = self.y1 + (self.y2 - self.y1) * t + random.uniform(-15, 15)
            segments.append((mx, my))
        segments.append((self.x2, self.y2))
        return segments

    def update(self):
        self.life -= 0.05
        if random.random() < 0.3:
            self.segments = self._generate_segments()
        return self.life > 0


class SplashScreen(QWidget):
    """Animated splash screen."""

    def __init__(self, on_finished=None):
        super().__init__()
        self.on_finished = on_finished
        self._opacity = 1.0
        self._progress = 0.0
        self._title_chars = 0
        self._status_text = "Initializing..."
        self._phase = 0  # 0=fade-in, 1=loading, 2=fade-out
        self._fade_in = 0.0
        self._logo_opacity = 0.0
        self._title_opacity = 0.0

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(800, 500)

        # Center on screen
        screen = self.screen().geometry() if self.screen() else QRectF(0, 0, 1920, 1080)
        self.move(
            int(screen.x() + (screen.width() - 800) / 2),
            int(screen.y() + (screen.height() - 500) / 2),
        )

        # Load assets
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        splash_path = os.path.join(base, "splash.png")
        self._bg = QPixmap(splash_path) if os.path.exists(splash_path) else None

        robotika_path = os.path.join(base, "logo_robotika.svg")
        self._robotika_svg = QSvgRenderer(robotika_path) if os.path.exists(robotika_path) else None

        nkz_path = os.path.join(base, "logo_nkz.svg")
        self._nkz_svg = QSvgRenderer(nkz_path) if os.path.exists(nkz_path) else None

        # Particles and arcs
        self._particles = []
        self._arcs = []

        # Colors
        self._colors = [
            QColor(34, 197, 94),    # green
            QColor(59, 130, 246),   # blue
            QColor(234, 179, 8),    # yellow
            QColor(0, 200, 200),    # cyan
        ]

        # Title
        self._full_title = "ModbusTool"

        # Status messages timeline
        self._messages = [
            (0.0, "Initializing Modbus engine..."),
            (0.25, "Loading device profiles..."),
            (0.50, "Detecting serial ports..."),
            (0.75, "Preparing interface..."),
            (0.90, "Starting GUI..."),
        ]

        # Animation timer — 30fps
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

        # Phase timeline
        self._tick_count = 0
        self._total_ticks = 100  # ~3.3 seconds at 30fps

    def _tick(self):
        self._tick_count += 1
        t = self._tick_count / self._total_ticks

        # Phase control
        if t < 0.15:
            # Fade in
            self._fade_in = min(1.0, t / 0.15)
            self._logo_opacity = 0.0
            self._title_opacity = 0.0
            self._progress = 0.0
        elif t < 0.30:
            # Logos appear
            self._fade_in = 1.0
            self._logo_opacity = min(1.0, (t - 0.15) / 0.15)
            self._title_opacity = 0.0
        elif t < 0.45:
            # Title typing
            self._logo_opacity = 1.0
            frac = (t - 0.30) / 0.15
            self._title_chars = int(frac * len(self._full_title))
            self._title_opacity = min(1.0, frac * 2)
        elif t < 0.90:
            # Progress bar filling
            self._title_chars = len(self._full_title)
            self._title_opacity = 1.0
            self._progress = (t - 0.45) / 0.45
            # Update status
            for threshold, msg in reversed(self._messages):
                if self._progress >= threshold:
                    self._status_text = msg
                    break
        elif t < 1.0:
            # Fade out
            self._progress = 1.0
            self._status_text = "Ready!"
            fade_t = (t - 0.90) / 0.10
            self._opacity = max(0.0, 1.0 - fade_t)
            self.setWindowOpacity(self._opacity)
        else:
            # Done
            self._timer.stop()
            self.close()
            if self.on_finished:
                self.on_finished()
            return

        # Spawn particles
        if t > 0.15 and random.random() < 0.6:
            x = random.uniform(50, 750)
            y = random.uniform(300, 460)
            color = random.choice(self._colors)
            self._particles.append(Particle(x, y, color))

        # Spawn arcs occasionally
        if t > 0.25 and random.random() < 0.08:
            x1 = random.uniform(100, 700)
            y1 = random.uniform(250, 400)
            x2 = x1 + random.uniform(-80, 80)
            y2 = y1 + random.uniform(-40, 40)
            color = random.choice(self._colors)
            self._arcs.append(ElectricArc(x1, y1, x2, y2, color))

        # Update particles
        self._particles = [p for p in self._particles if p.update()]
        self._arcs = [a for a in self._arcs if a.update()]

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()

        # Rounded rect clip
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 16, 16)
        p.setClipPath(path)

        # Background image
        if self._bg and not self._bg.isNull():
            scaled = self._bg.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                     Qt.TransformationMode.SmoothTransformation)
            x_off = (scaled.width() - w) // 2
            y_off = (scaled.height() - h) // 2
            p.drawPixmap(0, 0, scaled, x_off, y_off, w, h)

        # Dark overlay
        overlay = QColor(10, 15, 20, int(200 * self._fade_in))
        p.fillRect(0, 0, w, h, overlay)

        # Gradient edges
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(5, 10, 15, int(240 * self._fade_in)))
        grad.setColorAt(0.3, QColor(10, 15, 20, int(100 * self._fade_in)))
        grad.setColorAt(0.7, QColor(10, 15, 20, int(100 * self._fade_in)))
        grad.setColorAt(1.0, QColor(5, 10, 15, int(240 * self._fade_in)))
        p.fillRect(0, 0, w, h, grad)

        # Draw electric arcs
        for arc in self._arcs:
            color = QColor(arc.color)
            color.setAlphaF(arc.life * 0.7)
            pen = QPen(color, 1.5)
            p.setPen(pen)
            for i in range(len(arc.segments) - 1):
                x1, y1 = arc.segments[i]
                x2, y2 = arc.segments[i + 1]
                p.drawLine(int(x1), int(y1), int(x2), int(y2))
            # Glow
            color.setAlphaF(arc.life * 0.2)
            pen2 = QPen(color, 4)
            p.setPen(pen2)
            for i in range(len(arc.segments) - 1):
                x1, y1 = arc.segments[i]
                x2, y2 = arc.segments[i + 1]
                p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Draw particles
        for particle in self._particles:
            # Trail
            for tx, ty, tlife in particle.trail:
                c = QColor(particle.color)
                c.setAlphaF(tlife * particle.life * 0.3)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(c)
                s = particle.size * tlife * 0.5
                p.drawEllipse(QRectF(tx - s/2, ty - s/2, s, s))
            # Main dot
            c = QColor(particle.color)
            c.setAlphaF(particle.life * 0.9)
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            s = particle.size
            p.drawEllipse(QRectF(particle.x - s/2, particle.y - s/2, s, s))
            # Glow
            glow = QRadialGradient(particle.x, particle.y, s * 3)
            gc = QColor(particle.color)
            gc.setAlphaF(particle.life * 0.15)
            glow.setColorAt(0, gc)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(glow)
            p.drawEllipse(QRectF(particle.x - s*3, particle.y - s*3, s*6, s*6))

        # Logos
        if self._logo_opacity > 0:
            p.setOpacity(self._logo_opacity)

            # Robotika logo — left side
            if self._robotika_svg:
                logo_size = 70
                rx = 160 - logo_size // 2
                ry = 140
                self._robotika_svg.render(p, QRectF(rx, ry, logo_size, logo_size))

                # "Robotika.cloud" text
                p.setPen(QColor(255, 255, 255, int(200 * self._logo_opacity)))
                font = QFont("", 11)
                font.setWeight(QFont.Weight.Medium)
                p.setFont(font)
                p.drawText(QRectF(rx - 40, ry + logo_size + 5, logo_size + 80, 25),
                           Qt.AlignmentFlag.AlignCenter, "Robotika.cloud")

            # NKZ logo — right side
            if self._nkz_svg:
                nw, nh = 140, 36
                nx = 640 - nw // 2
                ny = 155
                self._nkz_svg.render(p, QRectF(nx, ny, nw, nh))

                p.setPen(QColor(255, 255, 255, int(200 * self._logo_opacity)))
                font = QFont("", 11)
                font.setWeight(QFont.Weight.Medium)
                p.setFont(font)
                p.drawText(QRectF(nx - 20, ny + nh + 8, nw + 40, 25),
                           Qt.AlignmentFlag.AlignCenter, "nkz-os.org")

            p.setOpacity(1.0)

        # Title — "ModbusTool"
        if self._title_opacity > 0:
            p.setOpacity(self._title_opacity)
            title_text = self._full_title[:self._title_chars]

            # Shadow
            font = QFont("", 36)
            font.setWeight(QFont.Weight.Bold)
            p.setFont(font)
            p.setPen(QColor(0, 0, 0, int(150 * self._title_opacity)))
            p.drawText(QRectF(2, 52, w, 80), Qt.AlignmentFlag.AlignCenter, title_text)

            # Main text with gradient-like effect
            p.setPen(QColor(255, 255, 255, int(255 * self._title_opacity)))
            p.drawText(QRectF(0, 50, w, 80), Qt.AlignmentFlag.AlignCenter, title_text)

            # Cursor blink during typing
            if self._title_chars < len(self._full_title):
                fm = QFontMetrics(font)
                tw = fm.horizontalAdvance(title_text)
                cx = (w - fm.horizontalAdvance(self._full_title)) / 2 + tw
                cy = 60
                if self._tick_count % 16 < 8:
                    p.setPen(QColor(34, 197, 94, int(200 * self._title_opacity)))
                    p.drawLine(int(cx + 2), int(cy), int(cx + 2), int(cy + 45))

            # Subtitle
            sub_font = QFont("", 12)
            p.setFont(sub_font)
            p.setPen(QColor(180, 200, 220, int(200 * self._title_opacity)))
            p.drawText(QRectF(0, 110, w, 30), Qt.AlignmentFlag.AlignCenter,
                       "Universal Modbus RTU/TCP Configuration & Monitoring")

            p.setOpacity(1.0)

        # Progress bar area
        if self._progress > 0:
            bar_x, bar_y = 100, 440
            bar_w, bar_h = w - 200, 6

            # Background
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 255, 30))
            p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 3, 3)

            # Fill
            fill_w = bar_w * min(1.0, self._progress)
            bar_grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
            bar_grad.setColorAt(0.0, QColor(34, 197, 94))
            bar_grad.setColorAt(0.5, QColor(59, 130, 246))
            bar_grad.setColorAt(1.0, QColor(234, 179, 8))
            p.setBrush(bar_grad)
            p.drawRoundedRect(QRectF(bar_x, bar_y, fill_w, bar_h), 3, 3)

            # Glow on tip
            if fill_w > 0:
                glow = QRadialGradient(bar_x + fill_w, bar_y + bar_h/2, 15)
                glow.setColorAt(0, QColor(255, 255, 255, 60))
                glow.setColorAt(1, QColor(0, 0, 0, 0))
                p.setBrush(glow)
                p.drawEllipse(QRectF(bar_x + fill_w - 15, bar_y - 12, 30, 30))

            # Status text
            p.setPen(QColor(180, 200, 220, 180))
            status_font = QFont("", 10)
            p.setFont(status_font)
            p.drawText(QRectF(bar_x, bar_y + 12, bar_w, 25),
                       Qt.AlignmentFlag.AlignCenter, self._status_text)

            # Percentage
            pct = int(self._progress * 100)
            p.drawText(QRectF(bar_x, bar_y - 20, bar_w, 20),
                       Qt.AlignmentFlag.AlignRight, f"{pct}%")

        # Border glow
        p.setClipPath(path)
        pen = QPen(QColor(34, 197, 94, int(80 * self._fade_in)), 2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 16, 16)

        p.end()

    def mousePressEvent(self, event):
        """Click to skip splash."""
        self._tick_count = int(self._total_ticks * 0.90)
