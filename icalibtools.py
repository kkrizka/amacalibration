import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

import glob, re

# Ideal limits for each OpAmpGain setting
# key is floor(OA/2), value is in Amp
ILIMITS={0: 1e-5,
         1: 3.7e-4,
         2: 2.5e-3,
         3: 3e-3}


def currentcalib(subdata, m, b, Voff, RI):
    Rtot=(subdata.ResistorValue+60+RI)
    return ((Rtot*(m*subdata.ADCvalue+b)+Voff)/(subdata.ResistorValue+60)).tolist()

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

def calibrate(data, fixCalib=True):
    calibs=pd.DataFrame(columns=['AMAC','Channel','BandgapControl','RampGain','OpAmpGain','m','b','Voff','RI'])

    for amackey,amacgroup in data.groupby('AMAC'):
        for chkey,chgroup in amacgroup.groupby('Channel'):
            for bgkey,bggroup in chgroup.groupby('BandgapControl'):
                for rgkey,rggroup in bggroup.groupby('RampGain'):
                    for oakey,oagroup in rggroup.groupby('OpAmpGain'):
                        # Remove any saturated region
                        subdata=oagroup[oagroup.InputCurrent<ILIMITS.get(oakey/2,1)].dropna()

                        if fixCalib:
                            # Initial fit using a linear relationship
                            Voff=-0.1
                            RI=50
                            CorrectedInputCurrent=(subdata.InputCurrent*(subdata.ResistorValue+60)-Voff)/((subdata.ResistorValue+60)+RI)
                            m,b=np.polyfit(pd.to_numeric(subdata.ADCvalue),CorrectedInputCurrent,1)

                            # Filter out bad guys, pass 1
                            filtsubdata=subdata[abs(subdata.ADCvalue-(CorrectedInputCurrent-b)/m)<512]
                            popt, pcov = curve_fit(currentcalib, filtsubdata, filtsubdata.InputCurrent,p0=(m,b,Voff,RI),bounds=((0,-np.inf,-np.inf,0),(np.inf,np.inf,np.inf,np.inf)))
                            m,b,Voff,RI=popt
                            CorrectedInputCurrent=(subdata.InputCurrent*(subdata.ResistorValue+60)-Voff)/((subdata.ResistorValue+60)+RI)

                            # Filter out bad guys, pass 2
                            filtsubdata=subdata[abs(subdata.ADCvalue-(CorrectedInputCurrent-b)/m)<8]
                            filtCorrectedInputCurrent=(filtsubdata.InputCurrent*(filtsubdata.ResistorValue+60)-Voff)/((filtsubdata.ResistorValue+60)+RI)
                            popt, pcov = curve_fit(currentcalib, filtsubdata, filtsubdata.InputCurrent,p0=(m,b,Voff,RI),bounds=((0,-np.inf,-np.inf,0),(np.inf,np.inf,np.inf,np.inf)))
                            m,b,Voff,RI=popt
                            
                            
                        else:
                            Voff=-0.1
                            RI=50
                            CorrectedInputCurrent=(subdata.InputCurrent*(subdata.ResistorValue+60)-Voff)/((subdata.ResistorValue+60)+RI)
                            m,b=np.polyfit(pd.to_numeric(subdata.ADCvalue),CorrectedInputCurrent,1)

                            # Filter out bad guys
                            filtsubdata=subdata[abs(subdata.ADCvalue-(CorrectedInputCurrent-b)/m)<16]
                            filtCorrectedInputCurrent=(filtsubdata.InputCurrent*(filtsubdata.ResistorValue+60)-Voff)/((filtsubdata.ResistorValue+60)+RI)
                            m,b=np.polyfit(pd.to_numeric(filtsubdata.ADCvalue),filtCorrectedInputCurrent,1)

                        # Save the results
                        calibs=calibs.append({'AMAC':amackey,
                                              'Channel':chkey,
                                              'BandgapControl':bgkey,
                                              'RampGain':rgkey,
                                              'OpAmpGain':oakey,
                                              'm':m,
                                              'b':b,
                                              'Voff':Voff,
                                              'RI':RI},
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

def plot_calibration(data,calib,AMAC=None,BG=10,RG=3,OA=5):
    if AMAC!=None:
        data =data [data .AMAC==AMAC]
        calib=calib[calib.AMAC==AMAC]

    data =data [(data .BandgapControl==BG)&(data .RampGain==RG)&(data .OpAmpGain==OA)]
    calib=calib[(calib.BandgapControl==BG)&(calib.RampGain==RG)&(calib.OpAmpGain==OA)]

    for amackey,amacgroup in data.groupby('AMAC'):
        for bgkey,bggroup in amacgroup.groupby('BandgapControl'):
            for rgkey,rggroup in bggroup.groupby('RampGain'):
                for oakey,oagroup in rggroup.groupby('OpAmpGain'):
                    for chkey,chgroup in oagroup.groupby('Channel'):
                        # Retrieve the calibration
                        thiscalib=calib[(calib.AMAC==amackey)&(calib.BandgapControl==bgkey)&(calib.RampGain==rgkey)&(calib.OpAmpGain==oakey)&(calib.Channel==chkey)]
                        m=thiscalib.m.iloc[0]
                        b=thiscalib.b.iloc[0]

                        Voff=thiscalib.Voff.iloc[0]
                        RI=thiscalib.RI.iloc[0]

                        # Apply corrections
                        CorrectedInputCurrent=(chgroup.InputCurrent*(chgroup.ResistorValue+60)-Voff)/((chgroup.ResistorValue+60)+RI)

                        # Get x limit
                        xlim=ILIMITS.get(oakey/2,1)*1e3

                        # Plot the calibration
                        plt.subplots_adjust(hspace=0.,wspace=0.)

                        plt.subplot2grid((3,3), (0,0), rowspan=2, colspan=3)
                        plt.semilogx(CorrectedInputCurrent*1e3,chgroup.ADCvalue,'.k')
                        plt.semilogx(CorrectedInputCurrent*1e3,(CorrectedInputCurrent-b)/m,'--b')
                        plt.ylabel('ADC counts')
                        plt.xlim(1e-4,xlim)
                        plt.ylim(0,1024)
                        plt.xticks([])
                        plt.title('%s, %s, Bandgap Control = %d, Ramp Gain = %d, OpAmp Gain = %d'%(amackey,chkey,BG,RG,OA))

                        info=[]
                        info.append('I = m ADC + b')
                        info.append('m = %0.2f $\mu$A/count'%(m*1e6))
                        info.append('b = %0.2f mA'%(b*1e3))
                        info.append('R$_{int}$ %0.1f $\Omega$'%(RI))
                        info.append('V$_{off}$ %0.1f mV'%(Voff*1e3))
                        plt.text(1.5e-4,500,'\n'.join(info),multialignment='left')

                        plt.subplot2grid((3,3), (2,0), rowspan=1, colspan=3)
                        resid=chgroup.ADCvalue-(CorrectedInputCurrent-b)/m
                        plt.semilogx(CorrectedInputCurrent*1e3,resid,'.k')
                        plt.semilogx([1e-4,3],[0,0],'--b')
                        plt.xlim(1e-4,xlim)
                        plt.ylim(-10,10)
                        plt.ylabel('Fit-Data')
                        plt.xlabel('Corrected Input Current [mA]')

                        plt.show()
    
