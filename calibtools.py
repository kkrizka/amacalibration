import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import glob, re

def filter_bad_data(data):
    filtdata=pd.DataFrame(data=None, columns=data.columns,index=data.index)
    for amackey,amacgroup in data.groupby('AMAC'):
        for bgkey,bggroup in amacgroup.groupby('BandgapControl'):
            for rgkey,rggroup in bggroup.groupby('RampGain'):
                for chkey,chgroup in rggroup.groupby('Channel'):
                    m,b=np.polyfit(chgroup.ADCvalue,chgroup.InputVoltage,1)

                    # Filter out bad guys
                    filtdata=filtdata.append(chgroup[abs(chgroup.ADCvalue-(chgroup.InputVoltage-b)/m)<8])
    return filtdata

def calibrate(data):
    calibs=pd.DataFrame(columns=['AMAC','Channel','BandgapControl','RampGain','m','b'])

    for amackey,amacgroup in data.groupby('AMAC'):
        for chkey,chgroup in amacgroup.groupby('Channel'):
            for bgkey,bggroup in chgroup.groupby('BandgapControl'):
                for rgkey,rggroup in bggroup.groupby('RampGain'):
                    m,b=np.polyfit(pd.to_numeric(rggroup.ADCvalue),rggroup.InputVoltage,1)

                    # Filter out bad guys
                    filtchgroup=chgroup[abs(chgroup.ADCvalue-(chgroup.InputVoltage-b)/m)<16]
                    m,b=np.polyfit(pd.to_numeric(filtchgroup.ADCvalue),filtchgroup.InputVoltage,1)

                    # Save the results
                    calibs=calibs.append({'AMAC':amackey,
                                          'Channel':chkey,
                                          'BandgapControl':bgkey,
                                          'RampGain':rgkey,
                                          'm':m,
                                          'b':b},
                                         ignore_index=True)

    return calibs

def convert(count,calib,AMAC=None,BG=10,RG=3,Channel=None):
    if AMAC   !=None: calib=calib[calib.AMAC          ==AMAC   ]
    if Channel!=None: calib=calib[calib.Channel       ==Channel]
    if BG     !=None: calib=calib[calib.BandgapControl==BG     ]
    if RG     !=None: calib=calib[calib.RampGain      ==RG     ]

    m=calib.m.iloc[0]
    b=calib.b.iloc[0]

    return m*count+b

def plot_calibration(data,calib,AMAC=None,BG=10,RG=3):
    if AMAC!=None:
        print(AMAC)
        data =data [data .AMAC==AMAC]
        calib=calib[calib.AMAC==AMAC]

    data =data [(data .BandgapControl==BG)&(data .RampGain==RG)]
    calib=calib[(calib.BandgapControl==BG)&(calib.RampGain==RG)]

    for amackey,amacgroup in data.groupby('AMAC'):
        for bgkey,bggroup in amacgroup.groupby('BandgapControl'):
            for rgkey,rggroup in bggroup.groupby('RampGain'):
                for chkey,chgroup in rggroup.groupby('Channel'):
                    # Retrieve the calibration
                    thiscalib=calib[(calib.AMAC==amackey)&(calib.BandgapControl==bgkey)&(calib.RampGain==rgkey)&(calib.Channel==chkey)]
                    m=thiscalib.m.iloc[0]
                    b=thiscalib.b.iloc[0]

                    # Plot the calibration
                    plt.subplots_adjust(hspace=0.,wspace=0.)

                    plt.subplot2grid((3,3), (0,0), rowspan=2, colspan=3)
                    plt.plot(chgroup.InputVoltage,chgroup.ADCvalue,'.k')
                    plt.plot(chgroup.InputVoltage,(chgroup.InputVoltage-b)/m,'--b')
                    plt.ylabel('ADC counts')
                    plt.xlim(0,1.2)
                    plt.ylim(0,1024)
                    plt.xticks([])
                    plt.title('%s, %s, Ramp Gain = %d, Bandgap Control = %d'%(amackey,chkey,RG,BG))
                    plt.text(0.1,1,'V = m ADC + b')
                    plt.text(0.1,0.9,'m = %0.2f mV/count'%(m*1000))
                    plt.text(0.1,0.8,'b = %0.2f mV'%(b*1000))

                    plt.subplot2grid((3,3), (2,0), rowspan=1, colspan=3)
                    resid=(chgroup.InputVoltage-b)/m-chgroup.ADCvalue
                    plt.plot(chgroup.InputVoltage,resid,'-b')
                    plt.plot([0,1.2],[0,0],'--k')
                    plt.xlim(0,1.2)
                    plt.ylim(-10,10)
                    plt.ylabel('Calib-Input [mV]')
                    plt.xlabel('Input Voltage [V]')
                    plt.text(0.1,5,'diff %0.2f $\pm$ %0.2f mV'%(resid.mean()*1000,resid.std()*1000))
                    plt.text(0.5,5,'maxdiff %d mV'%((max(abs(resid.max()),abs(resid.min()))*1000)))

                    plt.show()
    
def test_calibrate_perchip_perchannel(data,calib,AMAC=None,BG=10,RG=3):
    if AMAC!=None: data=data[data.AMAC==AMAC]
    data=data[(data.BandgapControl==BG)&(data.RampGain==RG)]

    for amackey,amacgroup in data.groupby('AMAC'):
        for bgkey,bggroup in amacgroup.groupby('BandgapControl'):
            for rgkey,rggroup in bggroup.groupby('RampGain'):
                for chkey,chgroup in rggroup.groupby('Channel'):
                    calibsource=calib[(calib.AMAC==amackey)&(calib.BandgapControl==bgkey)&(calib.RampGain==rgkey)&(calib.Channel==chkey)]
                    m=calibsource.m.iloc[0]
                    b=calibsource.b.iloc[0]

                    plot_calibration(chgroup,m,b)

def test_calibrate_perchip_perside(data,calib,AMAC=None,BG=10,RG=3):
    if AMAC!=None: data=data[data.AMAC==AMAC]
    data=data[(data.BandgapControl==BG)&(data.RampGain==RG)]

    for amackey,amacgroup in data.groupby('AMAC'):
        for bgkey,bggroup in amacgroup.groupby('BandgapControl'):
            for rgkey,rggroup in bggroup.groupby('RampGain'):
                for chkey,chgroup in rggroup.groupby('Channel'):
                    chcalibkey='CH0_L' if '_L' in chkey else 'CH0_R'
                    calibsource=calib[(calib.AMAC==amackey)&(calib.BandgapControl==bgkey)&(calib.RampGain==rgkey)&(calib.Channel==chcalibkey)]
                    m=calibsource.m.iloc[0]
                    b=calibsource.b.iloc[0]

                    plot_calibration(chgroup,m,b)

def test_calibrate_perchip(data,calib,AMAC=None,BG=10,RG=3,ch='CH0_R'):
    if AMAC!=None: data=data[data.AMAC==AMAC]
    data=data[(data.BandgapControl==BG)&(data.RampGain==RG)]

    for amackey,amacgroup in data.groupby('AMAC'):
        for bgkey,bggroup in amacgroup.groupby('BandgapControl'):
            for rgkey,rggroup in bggroup.groupby('RampGain'):
                for chkey,chgroup in rggroup.groupby('Channel'):
                    calibsource=calib[(calib.AMAC==amackey)&(calib.BandgapControl==bgkey)&(calib.RampGain==rgkey)&(calib.Channel=='CH0_R')]
                    m=calibsource.m.iloc[0]
                    b=calibsource.b.iloc[0]

                    plot_calibration(chgroup,m,b)
