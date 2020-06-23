#/bin/bash

WIDTH=30
HEIGHT=30

inkscape --export-png=exitToolbox.png --export-area-page -w $WIDTH -h $HEIGHT exit_to_app-24px.svg
inkscape --export-png=newJob.png --export-area-page -w $WIDTH -h $HEIGHT  add-24px.svg
inkscape --export-png=loadJob.png --export-area-page -w $WIDTH -h $HEIGHT  load_alt-24px.svg
inkscape --export-png=reloadJob.png --export-area-page -w $WIDTH -h $HEIGHT  restore-24px.svg
inkscape --export-png=closeJob.png --export-area-page -w $WIDTH -h $HEIGHT  close-24px.svg
inkscape --export-png=saveJob.png --export-area-page -w $WIDTH -h $HEIGHT  save_alt-24px.svg
inkscape --export-png=saveALL.png --export-area-page -w $WIDTH -h $HEIGHT  saveALL-24px.svg
inkscape --export-png=saveSIG.png --export-area-page -w $WIDTH -h $HEIGHT  saveSIG-24px.svg
inkscape --export-png=saveB2B.png --export-area-page -w $WIDTH -h $HEIGHT  saveB2B-24px.svg

inkscape --export-png=importOP.png --export-area-page -w $WIDTH -h $HEIGHT  construction-24px.svg


