import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from scipy.fftpack import fft, ifft

import datetime
import glob, re
import os.path

from IPython.display import HTML, display

import report
import calibtools

re_amac=re.compile('PB_(AMAC_[A-Z][0-9]+)')

class CoilMeasurement:
    def __init__(self,path):
        self.path=path

        self.volt=pd.read_csv(path,sep=' ')

        self.fft=None
        T=self.volt.time.iloc[1]
        N=len(self.volt.index)        
        yf = 2.0/N * np.abs(fft(self.volt.coil)[0:N//2])
        xf = np.linspace(0.0, 1.0/(2.0*T), N//2)*1e-6
        self.fft=pd.DataFrame(data={'freq':xf,'ampl':yf})



class Reports:
    def __init__(self,reports):
        self.names   =[r.name for r in reports]

        self.vin   =pd.concat([r.vin    for r in reports], ignore_index=True) if len(reports)>0 else None
        self.viniin=pd.concat([r.viniin for r in reports], ignore_index=True) if len(reports)>0 else None
        self.dcdceff=pd.concat([r.dcdceff for r in reports], ignore_index=True) if len(reports)>0 else None
        self.ileak=pd.concat([r.ileak for r in reports], ignore_index=True) if len(reports)>0 else None
        self.bgo=pd.concat([r.bgo for r in reports], ignore_index=True) if len(reports)>0 else None

    def append(self,r):
        self.names.append(r.name)

        self.vin=pd.concat([r.vin, self.vin], ignore_index=True) if self.vin is not None else r.vin
        self.dcdceff=pd.concat([r.dcdceff, self.dcdceff], ignore_index=True) if self.dcdceff is not None else r.dcdceff
        self.ileak=pd.concat([r.ileak, self.ileak], ignore_index=True) if self.ileak is not None else r.ileak
        self.bgo=pd.concat([r.bgo, self.bgo], ignore_index=True) if self.bgo is not None else r.bgo


class Report:
    def __init__(self,name):
        self.name=name

        self.amac=None
        self.calib=None

        self.general=None
        self.otaleft=None
        self.otaright=None
        self.dvdd2=None
        self.bgo=None
        self.Ibase=None

        self.vin=None
        self.viniin=None
        self.dcdceff=None
        self.ileak=None
        self.bgo=None
        self.coil_lvon =None
        self.coil_lvoff=None

        self.load_calib()

        self.load_general()
        self.load_vin()
        self.load_viniin()
        self.load_dcdceff()
        self.load_ileak()
        #self.load_bgo()
        self.load_coil()

    def load_general(self):
        #OTALEFT OTARIGHT DVDD2 BGO InBase

        datapath='pblog/{PB}_General.log'.format(PB=self.name)
        data=pd.DataFrame()
        if os.path.exists(datapath):
            data=pd.read_csv(datapath,sep=' ')
            data['PB']=self.name

            self.otaleft =data.OTALEFT.iloc[0]
            self.otaright=data.OTARIGHT.iloc[0]
            self.dvdd2   =data.DVDD2.iloc[0]
            self.bgo     =int(data.BGO.iloc[0])
            self.Ibase   =data.InBase.iloc[0]

        self.general=data

    def render_general(self):
        rows=['<td><b>OTA left</b></td><td>{}</td>'.format(self.otaleft),
              '<td><b>OTA right</b></td><td>{}</td>'.format(self.otaright),
              '<td><b>DVD/2</b></td><td>{}</td>'.format(self.dvdd2),
              '<td><b>BGO</b></td><td>{}</td>'.format(self.bgo),
              '<td><b>Ibase</b></td><td>{}</td>'.format(self.Ibase)]
        html='<html><body><table><tr><th></th><th>AMAC [counts]</th></tr>%s</table></body></html>'%(''.join(['<tr>{}</tr>'.format(row) for row in rows]))
        display(HTML(html))

    def load_calib(self):
        amac_match=re_amac.match(self.name)
        if amac_match!=None:
            self.amac=report.Report(amac_match.group(1))
            self.calib=calibtools.calibrate(self.amac.calib)

    def load_vin(self):
        datapath='pblog/{PB}_VIN.log'.format(PB=self.name)
        data=pd.DataFrame()
        if os.path.exists(datapath):
            data=pd.read_csv(datapath,sep=' ')
            data['PB']=self.name
            R1=90.9
            R2=10
            g=(R1+R2)/R2
            data['VinCalib']=data.apply(lambda row: calibtools.convert(row.VinADC,self.calib,Channel='CH0_R',BG=10,RG=3)*g, axis=1)
        self.vin=data

    def render_vin(self):
        plt.subplots_adjust(hspace=0.,wspace=0.)

        plt.subplot2grid((3,3), (0,0), rowspan=2, colspan=3)
        plt.plot(self.vin.Vin,self.vin.VinCalib,'.k')
        plt.plot(self.vin.Vin,self.vin.Vin     ,'--b')
        plt.ylabel('AMAC Measurement [V]')
        plt.xlim(5.5,12.5)
        plt.ylim(5.5,12.5)                                                                                                                                                                               
        plt.xticks([])                                                                                                                                                                                 
        plt.title(self.name)

        plt.subplot2grid((3,3), (2,0), rowspan=1, colspan=3)
        resid=(self.vin.VinCalib-self.vin.Vin)/self.vin.Vin
        plt.plot(self.vin.Vin,resid,'.k')                                                                                                                                                  
        plt.plot([5.5,12.5],[0,0],'--b')                                                                                                                                                                  
        plt.xlim(5.5,12.5)
        plt.ylim(-0.1,0.1)
        plt.ylabel('(AMAC-PS)/PS')
        plt.xlabel('Input Voltage [V]')

    def load_dcdceff(self):
        #Rf=499e3
        #Rg=200e3
        Rf=500e3
        Rg=20e3
        shunt=0.008
        G=Rf/Rg

        datapath='pblog/{PB}_DCDCEfficiency.log'.format(PB=self.name)
        data=pd.DataFrame()

        Ibase=self.Ibase if self.Ibase!=None else 0.4

        if os.path.exists(datapath):
            data=pd.read_csv(datapath,sep=' ')
            data['PB']=self.name
            data['IoutCalib']=data.apply(lambda row: calibtools.convert(row.IoutADC,self.calib,Channel='CH1_R',BG=10,RG=3), axis=1)
            data['IoutAMAC']=data['IoutCalib']/G/0.008*1000
            #data['eff']=(data.Iout/1000)*(data.Vout/1000)/(data.Iin-Ibase)/(data.Vin*10)
            data['eff']=(data.Iout/1000)*(1.5)/(data.Iin-Ibase)/(11)

        self.dcdceff=data

    def render_dcdceff(self):
        eff2A=self.dcdceff[self.dcdceff.Iout==2000].eff.iloc[0]

        plt.plot(self.dcdceff.Iout,self.dcdceff.eff)
        plt.text(2000,eff2A+0.01,'{:0.0f}% @ 2A'.format(eff2A*100))
        plt.xlim(0,4000)
        plt.ylim(0,1)
        plt.xlabel('Output Current [mA]')
        plt.ylabel('Efficiency')
        plt.title(self.name)

    def render_iout(self):
        plt.subplots_adjust(hspace=0.,wspace=0.)

        plt.subplot2grid((3,3), (0,0), rowspan=2, colspan=3)
        plt.plot(self.dcdceff.Iout,self.dcdceff.IoutAMAC,'.k')
        plt.plot(self.dcdceff.Iout,self.dcdceff.Iout    ,'--b')
        plt.ylabel('AMAC Measurement [mA]')
        plt.xlim(0,4000)
        plt.ylim(0,4000)
        plt.xticks([])                                                                                                                                                                                 
        plt.title(self.name)

        plt.subplot2grid((3,3), (2,0), rowspan=1, colspan=3)
        resid=(self.dcdceff.IoutAMAC-self.dcdceff.Iout)/self.dcdceff.Iout
        plt.plot(self.dcdceff.Iout,resid,'.k')                                                                                                                                                  
        plt.plot([0,4000],[0,0],'--b')                                                                                                                                                                  
        plt.xlim(0,4000)
        plt.ylim(-1,1)
        plt.ylabel('(AMAC-PS)/PS')
        plt.xlabel('Output Current [mA]')

    def load_ileak(self):
        datapath='pblog/{PB}_Ileak.log'.format(PB=self.name)
        data=pd.DataFrame()
        if os.path.exists(datapath):
            data=pd.read_csv(datapath,sep=' ')
            data['PB']=self.name
        self.ileak=data

    def render_ileak(self):
        plt.semilogx(self.ileak.Ileak,self.ileak.OpAmpGain0,label='OpAmpGain0')
        plt.semilogx(self.ileak.Ileak,self.ileak.OpAmpGain1,label='OpAmpGain1')
        plt.semilogx(self.ileak.Ileak,self.ileak.OpAmpGain2,label='OpAmpGain2')
        plt.semilogx(self.ileak.Ileak,self.ileak.OpAmpGain4,label='OpAmpGain4')
        plt.semilogx(self.ileak.Ileak,self.ileak.OpAmpGain8,label='OpAmpGain8')
        plt.xlabel('Ileak [mA]')
        plt.ylabel('Ileak [counts]')
        plt.title(self.name)
        plt.legend(frameon=False)

    def load_bgo(self):
        datapath='pblog/{PB}_Bandgap.log'.format(PB=self.name)
        data=pd.DataFrame()
        if os.path.exists(datapath):
            data=pd.read_csv(datapath,sep=' ')
            data['PB']=self.name
        self.bgo=data

    def render_bgo(self):
        plt.plot(self.bgo.BandgapControl,self.bgo.Voltage)
        plt.xlabel('BandgapControl')
        plt.ylabel('Bandgap Voltage [V]')
        plt.title(self.name)

    def load_viniin(self):
        datapath='pblog/{PB}_VinIin.log'.format(PB=self.name)
        data=pd.DataFrame()
        if os.path.exists(datapath):
            data=pd.read_csv(datapath,sep='\t')
            data['PB']=self.name
        self.viniin=data

    def render_viniin(self):
        plt.plot(self.viniin.Vin,self.viniin.Iin)
        plt.xlim(4,4.5)
        plt.ylim(0,1)
        plt.ylabel('Input Current [A]')
        plt.xlabel('Input Voltage [V]')

    def load_coil(self):
        datapath='pblog/{PB}_CoilLVON.log'.format(PB=self.name)
        if os.path.exists(datapath):
            self.coil_lvon=CoilMeasurement(datapath)

        datapath='pblog/{PB}_CoilLVOFF.log'.format(PB=self.name)
        if os.path.exists(datapath):
            self.coil_lvoff=CoilMeasurement(datapath)
    
    def render_coil(self):
        plt.plot(self.coil_lvon.volt.time*1e9 ,self.coil_lvon.volt.coil)
        plt.plot(self.coil_lvoff.volt.time*1e9,self.coil_lvoff.volt.coil)
        plt.xlim(0,5000)
        plt.ylim(-25,25)
        plt.xlabel('Time [ns]')
        plt.ylabel('Amplitude [mV]')
        plt.show()

        plt.loglog(self.coil_lvon .fft.freq,self.coil_lvon .fft.ampl)
        plt.loglog(self.coil_lvoff.fft.freq,self.coil_lvoff.fft.ampl)
        plt.xlim(1e-2,1e2)
        plt.ylim(1e-4,1e1)
        plt.xlabel('Frequency [MHz]')
        plt.ylabel('Amplitude')
        plt.show()

        plt.semilogx(self.coil_lvon.fft.freq,self.coil_lvon .fft.ampl-self.coil_lvoff.fft.ampl)
        plt.xlim(1e-2,1e2)
        plt.ylim(-1,6)
        plt.xlabel('Frequency [MHz]')
        plt.ylabel('LV ON - LV OFF')
        plt.show()
