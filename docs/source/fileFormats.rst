
File Formats
#####################


Input data file format
==========================

To import the signals to the platform, the collected data must be written in a text file.
Currently, two file formats are accepted:

  - EXP/DAT: specific to some experimental setups
  - CSV: More gereral file format.

The file formats are described below. The platform allow users to import not just CBFv, ABP and EtCO2 signals but other time dependent data according to the user's needs.

.. note:: New file formats can be included. If you have data in another format, contact us to create a file importer or converter.

EXP/DAT file
------------------------

Not all information in the file is necessary. The necessary lines are informed.

    .. code-block:: bash

        Patient Name: XXXXX                                          <-- not used
        birthday:DD:MM:YYYY                                          <-- not used
        Examination:DD:M:YYYY HH:MM:SS                               <-- loaded, but not used
        Sampling Rate: XXXHz                                         <-- necessary
        Time Sample <CH_0_label> <CH_1_label> ... <CH_N_label>       <-- necessary (separate labels with one TAB)
        HH:mm:ss:cs N <CH_0_unit> <CH_1_unit> ... <CH_N_unit>        <-- necessary (separate labels with one TAB)
        00:00:00:00 1 0 ###1 ###1 ... ###1                           <-- necessary
        ...
        00:00:00:00 N 0 ###N ###N ... ###N                           <-- necessary

Header
~~~~~~~~~~~~~~~~~~~~~~

The only necessary information in the header are:
 - Sampling rate, in Hz
 - channel labels
 - channel units

Tabulated data
~~~~~~~~~~~~~~~~~~~~~~

The tabulated data must be separated with tabs. The columns are:
    - **column 1 (not used):** Time instant following the format HH:mm:ss:cs. In total, this columns must have 11 characters

    - **column 2 (not used):** (integer) Sample number.

    - **next columns:** (float) channel data

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
        09:46:11:33	7	66	70	50.511	18.70
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

Please see the files in the examples directory.

CSV file
------------------------

The file is composed by tabulated data,  separated by semicolon (;)

    .. code-block:: bash

        Sampling Rate;XXXX                                 <-- Sampling frequency in Hertz
        <CH_0_label>;<CH_1_label>;...;<CH_N_label>         <-- Channel labels
        <CH_0_unit>;<CH_1_unit>;...;<CH_N_unit>            <-- Channel units
        00.00;00.00;...;00.00
        00.00;00.00;...;00.00
        00.00;00.00;...;00.00
        00.00;00.00;...;00.00
        ...

The rest of the file contains the numeric values, separated with semicolon (;).

**Example:** Dataset with 4 channels

    .. code-block:: bash

        Sampling Rate;100.00;;
        MCA L;MCA R;ABP;ETCO2
        cm/s;cm/s;mmHg;mmHg
        116.00;99.00;92.04;162.84
        56.00;46.00;44.88;81.36
        53.00;44.00;44.52;81.36
        53.00;41.00;44.16;81.36
        51.00;37.00;44.28;81.36
        47.00;34.00;43.88;81.72
        44.00;30.00;42.96;81.72
        41.00;27.00;42.76;81.48
        40.00;27.00;41.84;81.60
        40.00;27.00;41.84;81.48
        38.00;27.00;41.72;81.72
        38.00;27.00;41.44;81.36
        38.00;27.00;40.64;81.48
        ...

Please see the files in the examples directory.


Job files
==========================


The platform works with the concept of jobs. A job is composed by one input file containing the measurements and a sequence of operations. The job is saved in a text file (.job). The file contains a list of all operations, listed in the same order that they were applied to the data set.

 The contents of a .job file is presented in the example below.

**Example**

    .. code-block:: xml
    
        <?xml version='1.0' encoding='UTF-8'?>
        <job version="0.2">
          <inputFile type="CSV">healthy.csv</inputFile>         <!-- input file -->
          <operations imported="False">
            <preprocessing>
              <setType>                                         <!-- operation: set type of signal in channel 0 -->
                <type>CBFV_L</type>
                <channel>0</channel>
              </setType>
              <setLabel>                                        <!-- operation: set label of signal in channel 0 -->
                <label>CBFV_L</label>
                <channel>0</channel>
              </setLabel>
              <setUnit>                                         <!-- operation: set unit label of signal in channel 0 -->
                <unit>cm/s</unit>
                <channel>0</channel>
              </setUnit>
              <setType>
                <type>CBFV_R</type>
                <channel>1</channel>
              </setType>
              <setLabel>
                <label>CBFV_R</label>
                <channel>1</channel>
              </setLabel>
              <setUnit>
                <unit>cm/s</unit>
                <channel>1</channel>
              </setUnit>
              <setType>
                <type>ABP</type>
                <channel>2</channel>
              </setType>
              <setLabel>
                <label>ABP</label>
                <channel>2</channel>
              </setLabel>
              <setUnit>
                <unit>mmHg</unit>
                <channel>2</channel>
              </setUnit>
              <setType>
                <type>ETCO2</type>
                <channel>3</channel>
              </setType>
              <setLabel>
                <label>ETCO2</label>
                <channel>3</channel>
              </setLabel>
              <setUnit>
                <unit>mmHg</unit>
                <channel>3</channel>
              </setUnit>
              <synchronize>                                  <!-- operation: synchronize channels based on ABP fixed delay -->
                <method>fixedAPB</method>
                <ABPdelay_s>0.9</ABPdelay_s>
              </synchronize>
              <LPfilter>                                     <!-- operation: Channel 0 lowpass filter -->
                <method>movingAverage</method>
                <Ntaps>3</Ntaps>
                <channel>0</channel>
              </LPfilter>
              <LPfilter>
                <method>movingAverage</method>
                <Ntaps>3</Ntaps>
                <channel>1</channel>
              </LPfilter>
              <LPfilter>
                <method>movingAverage</method>
                <Ntaps>3</Ntaps>
                <channel>2</channel>
              </LPfilter>
              <LPfilter>
                <method>movingAverage</method>
                <Ntaps>3</Ntaps>
                <channel>3</channel>
              </LPfilter>
              <findRRmarks>                                     <!-- operation: R-R peak detection -->
                <refChannel>2</refChannel>
                <method>ampd</method>
                <findPeaks>True</findPeaks>
                <findValleys>False</findValleys>
              </findRRmarks>
              <B2Bcalc>                                         <!-- operation: Beat-to-beat extraction -->
                <resampleMethod>cubic</resampleMethod>
                <resampleRate_Hz>5.0</resampleRate_Hz>
              </B2Bcalc>
              <SIGsave>                                         <!-- operation: Save processed signals -->
                <channels>[0 1 2 3]</channels>
                <fileName>output.sig</fileName>
                <format>simple_text</format>
              </SIGsave>
              <B2Bsave>                                         <!-- operation: Save beat-to-beat signals -->
                <channels>[0 1 2 3]</channels>
                <fileName>output.b2b</fileName>
                <format>simple_text</format>
              </B2Bsave>
            </preprocessing>
          </operations>
        </job>


 .. Note:: The platform is responsible for creating the .job file. However, it is possible to edit the .job file directly in a text editor to modify the operations or reproduce the same operations in multiple input files. This might be useful, for example, to apply the same protocol to different cases or for studying the effects of changing their parameters to the same input file.
