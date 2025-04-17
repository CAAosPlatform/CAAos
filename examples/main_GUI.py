import sys

import platform

from PyQt5 import QtGui, QtWidgets

from CAAos.GUI.main_GUI import GuiMain

if sys.version_info.major == 2:
    sys.stdout.write('Sorry! This program requires Python 3.x\n')
    sys.exit(1)

app = QtWidgets.QApplication(sys.argv)
# print(QtWidgets.QStyleFactory.keys())

if platform.system() == 'Windows':
    # windows: ['windowsvista', 'Windows', 'Fusion']
    app.setStyle('Windows')

if platform.system() == 'Linux':
    # linux: ['Breeze', 'Oxygen', 'Windows', 'Fusion']
    app.setStyle('Breeze')

if platform.system() == 'Darwin':  # Mac
    # macintosh: ['macintosh', 'Windows', 'Fusion']
    app.setStyle('macintosh')

app.setWindowIcon(QtGui.QIcon('src/images/logo_32x32.png'))
ex = GuiMain()
sys.exit(app.exec_())
