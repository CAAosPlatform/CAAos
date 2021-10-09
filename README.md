
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4891862.svg)](https://doi.org/10.5281/zenodo.4891862)

Welcome to the official repository of CAAos Platform (Cerebral Autoregulation Assessment Open Source Platform)!

<p align="center">
<img src="docs/source/images/logo_800x591.png" width="600">
</p>

CAAos is an unified open source, cross-platform toolbox written in Python for processing and analysing cerebral autoregulation datasets from diverse clinical protocols and acquisition modalities. This is a new free software research tool that combines existing and novel methods for interactive visual inspection, batch processing and analysis of multichannel records. As open-source software, the source code is freely available for non-commercial use, reducing barriers to performing CA analysis, allowing inspection of the inner-workings of the algorithms and facilitating networked activities with common standards.

# Installation

## Windows users
Installation procedure is presented in this  [video tutorial](https://www.youtube.com/watch?v=_usZZhf4ggY).

## Linux users


### Conda/miniconda
If you use conda or miniconda, you can create a python environment for the platform with

~~~
conda create --name python38_CAAos python=3.8
conda activate python38_CAAos
pip install numpy matplotlib scipy PyQt5 lxml Pillow pyqtgraph six pytest
conda deactivate
~~~

Then you can run the platform with

~~~
conda activate python38_CAAos
cd /path/to/the/platform/src/
python main_GUI.py
~~~

If you want to close the virtual environment, type

~~~
conda deactivate
~~~

### virtual env

If you prefer using venv to create your python environment, make sure you have python >=3.8 and run.

~~~
python3 -m venv path/to/new/venv
source path/to/new/venv/bin/activate
pip install numpy matplotlib scipy PyQt5 lxml Pillow pyqtgraph six pytest
~~~

You might need to install python3.8-venv. For ubuntu:

~~~
sudo apt install python3.8-venv
~~~

Then you can run the platform with

~~~
source path/to/new/venv/bin/activate
cd /path/to/the/platform/src/
python main_GUI.py
~~~

If you want to close the virtual environment, type

~~~
deactivate
~~~

# Tutorials

Please visit our [YouTube channel](https://www.youtube.com/channel/UCDzdHse1rxFDlmmJX698jzg/featured) for tutorial videos.

# Documentation

The documentation is available here: <https://caaosplatform.github.io/CAAos>. We are constantly updating the documentation.

