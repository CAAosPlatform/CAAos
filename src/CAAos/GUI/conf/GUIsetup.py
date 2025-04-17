import pyqtgraph as pg

darkTheme = False

if darkTheme:
    pyQtConf = {  # Dark theme
        'backgroundColor': 'k', 'foregroundColor': 'w', 'textColor': (255, 255, 255),
        'plotColors': {'red': (255, 0, 0), 'green': (125, 221, 126), 'blue': (0, 170, 255), 'base': (255, 255, 255)},
        'linearRegionBrush': pg.mkBrush((200, 200, 200, 100)), 'linearRegionPen': pg.mkPen(color=(255, 0, 0, 255)), 'plotLineWidth': 1,
        'peakMarkSymbol': 'o', 'peakMarkSize': 5, 'peakMarkColor': (255, 0, 0), 'PlotLeftMargin': 60}
else:
    pyQtConf = {'backgroundColor': 'w', 'foregroundColor': 'k', 'textColor': (0, 0, 0),
                'plotColors': {'red': (255, 0, 0), 'green': (120, 255, 90), 'blue': (0, 100, 200), 'base': (0, 0, 0)},
                'linearRegionBrush': pg.mkBrush((50, 50, 50, 50)), 'linearRegionPen': pg.mkPen(color=(255, 0, 0, 255)), 'plotLineWidth': 1,
                'peakMarkSymbol': 'o', 'peakMarkSize': 5, 'peakMarkColor': (255, 0, 0), 'PlotLeftMargin': 60}

if pyQtConf['plotLineWidth'] == 1.0:
    pg.setConfigOption('antialias', False)  # turning it on will cause drop in performance
else:
    pg.setConfigOption('antialias', True)  # turning it on will cause drop in performance
pg.setConfigOption('background', pyQtConf['backgroundColor'])
pg.setConfigOption('foreground', pyQtConf['foregroundColor'])
