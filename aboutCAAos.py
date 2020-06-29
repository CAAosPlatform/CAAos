#!/usr/bin/python

# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

from patientData import patientData


class About(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(About, self).__init__(parent)

        self.initUI()

    def initUI(self):
        # create central widget
        self.centralwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle("About CAAos")

        # screen size and position
        self.resize(500, 600)
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # version
        lineVersion = QtWidgets.QLabel('CAAos v.%s' % patientData.getVersion())
        lineVersion.setAlignment(QtCore.Qt.AlignRight)
        lineVersion.setOpenExternalLinks(True)

        # make a link to the websites
        links = QtWidgets.QLabel('<a href=\"https://github.com/CAAosPlatform/CAAos\">CAAos Github</a> '
                                 '<a href=\"https://caaosplatform.github.io/CAAos/\">CAAos Home page</a>')
        links.setAlignment(QtCore.Qt.AlignRight)
        links.setOpenExternalLinks(True)

        # logo
        logo = QtWidgets.QLabel()
        logo.setPixmap(QtGui.QPixmap('./images/logo_800x591.png').scaled(400, 400, QtCore.Qt.KeepAspectRatio))
        logo.setAlignment(QtCore.Qt.AlignCenter)

        # authors
        authors = QtWidgets.QPlainTextEdit('CECS - Center for Engineering, Modeling and Applied Social Sciences\n'
                                           'Federal University of ABC (UFABC)\n'
                                           'São Bernardo do Campo - Brazil\n'
                                           '---------------------------------------------\n'
                                           '(alphabetical order)\n'
                                           'André Morilha\n'
                                           'Angela Salinet\n'
                                           'Fernando Moura\n'
                                           'Firmino\n'
                                           'João Salinet\n'
                                           'Pedro Santos\n'
                                           'Renata Romanelli')
        authors.setReadOnly(True)

        # license information text
        license = QtWidgets.QPlainTextEdit(open('LICENSE', 'r').read())
        license.setReadOnly(True)

        # credits
        credits = QtWidgets.QPlainTextEdit('Automatic Multiscale-based Peak Detection (AMPD)\nhttps://github.com/CAAosPlatform/CAAos\n-------\n'
                                           'Peak detection (MD)\nhttps://github.com/demotu/BMC\n-------\n')
        credits.setReadOnly(True)

        # create tabs
        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(authors, 'Authors')
        tabWidget.addTab(license, 'License')
        tabWidget.addTab(credits, 'Credits')

        vbox = QtWidgets.QVBoxLayout(self.centralwidget)
        vbox.addWidget(lineVersion)
        vbox.addWidget(links)
        vbox.addWidget(logo)
        vbox.addStretch()
        vbox.addWidget(tabWidget)
        vbox.addStretch()

        self.setLayout(vbox)

        self.show()
