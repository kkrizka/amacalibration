#!/usr/bin/env python 

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import glob
import re

import report

import icalibtools

re_generalparams=re.compile('log/(AMAC_[a-zA-Z0-9]+)_GeneralParams.log')

#
# Find all of the available AMAC tests
reports=[]
for path in glob.glob('log/AMAC_C03_GeneralParams.log'):
    match=re_generalparams.match(path)
    reports.append(report.Report(match.group(1)))
reports=report.Reports(reports)

#
# Perform the calibration
icalib=icalibtools.calibrate(reports.icalib,fixCalib=True)

#
# Save data
for amackey,amacgroup in icalib.groupby('AMAC'):
    amacgroup.to_csv('icalib_%s.csv'%amackey, index=False)

#
# Save pretty images
for ckey,cdata in icalib.groupby(['AMAC','Channel','BandgapControl','RampGain','OpAmpGain']):
    icalibtools.plot_calibration(reports.icalib,icalib,ckey[0],ckey[1],ckey[2],ckey[3])
    plt.show()
    plt.savefig('img/icalib_%s_%s_BandgapControl%d_RampGain%d_OpAmpGain%d.png'%ckey)
