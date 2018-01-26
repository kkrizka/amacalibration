#!/usr/bin/env python 

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import glob
import re

import report

import calibtools

re_generalparams=re.compile('log/(AMAC_[a-zA-Z0-9]+)_GeneralParams.log')

#
# Find all of the available AMAC tests
reports=[]
for path in glob.glob('log/AMAC_???_GeneralParams.log'):
    match=re_generalparams.match(path)
    reports.append(report.Report(match.group(1)))
reports=report.Reports(reports)

#
# Perform the calibration
calib=calibtools.calibrate(reports.calib)

calib.to_csv('calib.csv',index=False)

#
# Save pretty images
for ckey,cdata in calib.groupby(['AMAC','Channel','BandgapControl','RampGain']):
    calibtools.plot_calibration(reports.calib,calib,ckey[0],ckey[1],ckey[2],ckey[3])
    plt.show()
    plt.savefig('img/calib_%s_%s_BandgapControl%d_RampGain%d.png'%ckey)
