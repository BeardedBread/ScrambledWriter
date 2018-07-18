"""
This file contains the widget to animate the printing of a text with scrambled
garbage, similar to the text printing in the game N++ by Metanet.
Credits to them for this cool effect.

Requires pyqt5 and python3

Start the demo by typing in console:
python3 scramblewriter.py <filename> <speed> <delay>
"""

from PyQt5.Qt import QApplication
from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QWidget, QScrollArea, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import (QAbstractAnimation, QPropertyAnimation, pyqtProperty, pyqtSignal, Qt)
import sys
import random


class MessageLabel(QLabel):
    textChanged = pyqtSignal()

    def __init__(self, text, speed=20, delay=-1, parent=None):
        super().__init__(text, parent)

        self.setWordWrap(True)
        self.setContentsMargins(0, 0, 0, 0)
        # Text processing
        # Make sure the garbage does not exceed the length of actual text
        self.actual_text = text
        self.shown_text = ''
        if delay >= 0:
            self.delay = min(delay, len(self.actual_text))
        else:
            self.delay = len(self.actual_text)

        # Find out where the new paragraphs are so that it is retained
        self.splitpoints = []
        current_point = 0
        line_splits = self.actual_text.split('\n')
        for line in line_splits:
            current_point += len(line)
            self.splitpoints.append(current_point)
            current_point += 1

        # Set up the shown text length to be animated
        self.shown_length = 0
        self.anim = QPropertyAnimation(self, b'shown_length')
        self.anim.setDuration(len(self.actual_text) * speed)
        self.anim.setStartValue(0)
        self.anim.setEndValue(len(self.actual_text) + self.delay)

        self.setStyleSheet("""
                    color: rgb(0, 255, 0);
                """)

    @pyqtProperty(int)
    def shown_length(self):
        """
        # int : The value for the animation

        When the value is set, the text to be printed is generated accordingly.
        It determines whether actual text is to be printed, and retains the
        paragraphs when printing garbage.
        """
        return self._shown_length

    @shown_length.setter
    def shown_length(self, value):
        self._shown_length = value

        if value < self.delay:
            # All printed text should be garbage
            garbage = [chr(num) for num in
                       [random.choice(range(33, 127)) for _ in range(value)]]

            # Retain the paragraphs
            for num in self.splitpoints[:-1]:
                if num < value:
                    garbage[num] = '\n'

            self.setText(''.join(garbage))
        else:
            # Printed text contain some actual text
            garbage = [chr(num) for num in
                       [random.choice(range(33, 127)) for _ in
                        range(min(len(self.actual_text) + self.delay - value, self.delay))]]

            # Retain the paragraphs, but offset by the number of actual text
            non_garbage = value - self.delay
            for num in self.splitpoints[:-1]:
                if num - non_garbage > 0 and num < value:
                    garbage[num - non_garbage] = '\n'

            self.setText(self.actual_text[:value - self.delay] + ''.join(garbage))

        self.textChanged.emit()

    def toggle_anim(self, toggling):
        """
        Toggle the animation to be play forward or backward

        Parameters
        ----------
        toggling: bool
            True for forward, False for backward
        """
        if toggling:
            self.anim.setDirection(QAbstractAnimation.Forward)
        else:
            self.anim.setDirection(QAbstractAnimation.Backward)

        self.anim.start()


class MessageContainer(QWidget):
    sizeChanged = pyqtSignal(float)

    def resizeEvent(self, event):
        self.sizeChanged.emit(event.size().height())


class MessageDisplayer(QScrollArea):

    def __init__(self, speed=20, delay=-1, parent=None):
        super().__init__(parent=parent)

        self.displayer = MessageContainer()

        self.layout = QVBoxLayout(self.displayer)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(0)

        self.setWidget(self.displayer)
        self.setWidgetResizable(True)

        self.speed = speed
        self.delay = delay

        self.displayer.sizeChanged.connect(self.verticalScrollBar().setSliderPosition)
        self.setStyleSheet("""
                        background-color: rgb(0, 0, 0);
                        """)

    def insert_message(self, text):
        label = MessageLabel(text, speed=self.speed, delay=self.delay, parent=self)
        self.layout.addWidget(label)
        label.toggle_anim(True)

class MessageInput(QWidget):
    messageInputted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)

        self.prefix_label = QLabel('>', self)
        self.msg_input = QLineEdit(self)

        self.layout.addWidget(self.prefix_label)
        self.layout.addWidget(self.msg_input)
        self.msg_input.editingFinished.connect(self.send_message)

        self.setStyleSheet("""
                        border-top: 1px solid white;
                        color: rgb(0, 255, 0);                        
                        """)

    def send_message(self):
        self.messageInputted.emit(self.msg_input.text())
        self.msg_input.clear()

class AnimatedTextPrinter(QWidget):
    """
    Widget to gradually print text with scrambled garbage.
    """

    def __init__(self, text, speed=20, delay=-1, parent=None):
        """
        Create a widget containing a QLabel, which displays the text.
        Process the text and set up the QPropertyAnimation
        as well to animate the printing.

        Parameters
        ----------
        text : str
            The text to print
        speed : int
            The period at which a new character is printed
            The total time is calculated as length of text * speed
            0 means instant display, like a regular QLabel.
        delay : int
            The number of garbage to be printed before printing the actual text
        """
        # Setup the widget
        super().__init__(parent=parent)
        self.layout = QVBoxLayout(self)
        self.display = MessageDisplayer(speed, delay, parent=self)
        self.layout.addWidget(self.display)
        self.msg_input = MessageInput(self)
        self.layout.addWidget(self.msg_input)
        self.setGeometry(10, 10, 500, 300)
        self.parent = parent

        for txt in text.split('\n'):
            self.display.insert_message(txt)
        self.show()

        self.setStyleSheet("""
                        background-color: rgb(0, 0, 0);
                        """)

        self.msg_input.messageInputted.connect(self.display.insert_message)


class AnimatedFilePrinter(AnimatedTextPrinter):
    """
    A class to print text from file
    """
    def __init__(self, filename, speed=20, delay=-1, parent=None):
        """
        Similar to AnimatedText, but with an option to pass text file

        Parameters
        ----------
        file : str
            Directory of the text file to be read
        """
        with open(filename, 'r') as f:
            text = f.read()
        super().__init__(text.strip('\n'), speed=speed, delay=delay, parent=parent)


if __name__ == "__main__":
    # Set up the Qt Application
    app = 0
    app = QApplication(sys.argv)

    # Input checking
    input_param = sys.argv
    if len(input_param) < 2:
        input_param.append('20')
    if len(input_param) < 3:
        input_param.append('-1')
    print('Speed Per Char: {:s}ms\nNumber of Garbage: {:s}'.format(*input_param[1:]))

    # Create the animated printer and start the animation
    writer = AnimatedTextPrinter("Welcome to the printer", speed=int(input_param[1]), delay=int(input_param[2]))
    sys.exit(app.exec_())
