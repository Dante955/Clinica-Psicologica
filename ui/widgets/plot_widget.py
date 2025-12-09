# ui/widgets/plot_widget.py

import matplotlib
from PySide6.QtWidgets import QWidget, QVBoxLayout

# Asegúrate de que el backend QtAgg está seleccionado
matplotlib.use('QtAgg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

class MplPlotWidget(QWidget):
    """
    Un widget para incrustar un gráfico de Matplotlib en una aplicación PySide6.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. Crear la figura de Matplotlib y el canvas de Qt
        # La figura es el contenedor de nivel superior para todos los elementos del gráfico.
        self.figure = Figure(figsize=(5, 3), dpi=100)
        
        # El canvas es el widget que realmente dibuja la figura en la ventana de Qt.
        self.canvas = FigureCanvas(self.figure)
        
        # 2. Crear la barra de herramientas de navegación de Matplotlib
        self.toolbar = NavigationToolbar(self.canvas, self)

        # 3. Configurar el layout del widget
        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar) # Añadir la barra de herramientas
        layout.addWidget(self.canvas)  # Añadir el lienzo del gráfico

        self.setLayout(layout)

        # 4. Crear un gráfico de ejemplo para mostrar algo al inicio
        self.plot_example()

    def plot_example(self):
        """
        Dibuja un gráfico de ejemplo simple.
        """
        # Limpiar cualquier gráfico anterior
        self.figure.clear()

        # Crear un "Axes" (un subplot o área de trazado)
        ax = self.figure.add_subplot(111)
        
        # Generar datos de ejemplo (una función seno)
        x = np.linspace(0, 10, 100)
        y = np.sin(x)

        # Trazar los datos
        ax.plot(x, y, label='sin(x)')
        
        # Añadir títulos y etiquetas para que se vea profesional
        ax.set_title("Grafico de ungreso y salida de dinero")
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        ax.legend()
        ax.grid(True) # Añadir una cuadrícula

        # Asegurar que la figura se redibuje en el canvas
        self.canvas.draw()

    def plot_financial_data(self, data_x, data_y, title="Reporte Financiero"):
        """
        Un método de ejemplo para trazar datos financieros reales.
        Puedes llamar a este método desde fuera para actualizar el gráfico.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.plot(data_x, data_y, marker='o')
        
        ax.set_title(title)
        ax.set_xlabel("Fecha")
        
        # Rotar las etiquetas del eje x si son fechas para mejorar la legibilidad
        self.figure.autofmt_xdate()

        self.canvas.draw()