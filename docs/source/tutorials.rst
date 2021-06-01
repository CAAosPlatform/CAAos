
Tutorials
#####################



Main screen
**********************

The platform
==========================

The CAAos platform was developed in Python 3 language, aiming for a concise, easy to use experience. It is available under GNU GPLv3 license on `Github <https://github.com/CAAosPlatform/CAAos>`_. The installation package and instructions are also available, together with a demo data of two subjects (one healthy control and one stroke patient data), allowing users to operate the platform and its functionalities. :ref:`Figure 1<fig1>`  presents the home screen of the platform once it is launched.

    .. _fig1:

    .. figure:: ./images/Figura01.png
       :width: 800px
       :alt: Platform's home screen
       :align: center

       Figure 1: Platform’s home screen


Menu Entries
==========================

There are three main menu entries in the toolbar  inside the home screen
 (see Figure 1), being them:

 1) **File:** This tab enables the user to exit the platform;

 2) **Toolboxes:** This menu entry allows the user to initiate the patient’s autoregulation analysis by first performing the preprocessing steps, as described in 2.2, and then the cerebral autoregulation analysis;

 3) **Help:** This menu entry contains information about the platform, version, licenses, credits and authors. 
 
    .. _fig2:

    .. figure:: ./images/Figura02.png
       :width: 800px
       :alt: Platform's home screen
       :align: center

       Figure 2: Indication of the main tabs of the platform.


Usage
**********************

Collecting the Data
==========================

Before initiating CAAos platform, the user needs to collect the subject’s signals. The signals are the cerebral blood flow velocity (CBFv) and arterial blood pressure (ABP). Other signals such as end-tidal carbon dioxide (EtCO2) can also be uploaded. The first two signals are collected as presented below.


Input file format
**********************

To import the signals to the platform, the collected data must be written in a text file. The file must inform the sampling rate in which the signals were collected, and the data must be written in columns, separated with tabs.
This format allows users to import not just CBFv, ABP and EtCO2 signals but other time dependent data according to the user’s needs. The only information necessary are the Sampling rate (in Hz), column labels, units, and the numeric data. Patient name and birthday are not used. Examination date is loaded from the file but it is not currently used for anything.


    .. code-block:: bash
    
        Patient Name: XXXXX
        birthday:DD:MM:YYYY
        Examination:DD:M:YYYY HH:MM:SS
        Sampling Rate: XXXHz
        Time   Sample <CH_0_label> <CH_1_label> ... <CH_N_label>
        HH:mm:ss:ms N <CH_0_unit> <CH_1_unit> ... <CH_N_unit>
        00:00:00:00 0 0 xxx1 xxx2 ... xxxN
        00:00:00:00 0 0 yyy1 yyy2 ... yyyN

**Example:** Dataset with 4 channels


    .. code-block:: bash
    
        Patient Name: XXXXXXX
        birthday:00:00:0000
        Examination:00:0:0000 00:00:00
        Sampling Rate: 100Hz
        Time	Sample	CBFvL	CBFvR	ABP	ETCO2
        HH:mm:ss:ms	N	cm/s	cm/s	mmHg	mmHg
        09:46:11:26	0	108	118	53.938	20.75
        09:46:11:27	1	108	118	53.044	20.30
        09:46:11:28	2	108	118	51.405	19.80
        09:46:11:29	3	98	116	50.809	19.65
        09:46:11:30	4	97	116	50.362	19.45
        09:46:11:31	5	92	111	50.064	19.15
        09:46:11:32	6	68	78	49.915	19.00
        09:46:11:33	7	66	70	50.511	18.7	0
        09:46:11:34	8	65	70	50.064	18.60
        09:46:11:35	9	64	69	49.617	18.30
        09:46:11:36	10	64	68	49.021	18.15
        09:46:11:37	11	62	68	49.021	18.35
        09:46:11:38	12	59	68	49.17	18.35
        09:46:11:39	13	59	68	49.617	18.20
        09:46:11:40	14	59	68	49.617	18.15
        09:46:11:41	15	59	68	50.064	18.05
        09:46:11:42	16	59	68	49.319	17.70
        09:46:11:43	17	59	106	48.425	17.65
        ...
        


Preprocessing Toolbox
==========================



