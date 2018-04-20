import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import glob, re
import os.path

from IPython.display import HTML, display

import report
import calibtools

class Reports:
    def __init__(self,reports):
        self.names   =[r.name for r in reports]

        self.vin=pd.concat([r.vin for r in reports], ignore_index=True) if len(reports)>0 else None
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

        self.vin=None
        self.dcdceff=None
        self.ileak=None
        self.bgo=None
        self.load_calib()

        self.load_vin()
        self.load_dcdceff()
        self.load_ileak()
        self.load_bgo()

    def load_calib(self):
        self.amac=report.Report(self.name[3:])
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
        plt.plot(self.vin.Vin,self.vin.VinADC)
        plt.xlabel('Vin [V]')
        plt.ylabel('Vin [counts]')

    def load_dcdceff(self):
        #Rf=499e3
        #Rg=200e3
        Rf=500e3
        Rg=20e3
        shunt=0.008
        G=Rf/Rg

        datapath='pblog/{PB}_DCDCEfficiency.log'.format(PB=self.name)
        data=pd.DataFrame()
        Ibase=0.04
        if os.path.exists(datapath):
            data=pd.read_csv(datapath,sep=' ')
            data['PB']=self.name
            data['IoutCalib']=data.apply(lambda row: calibtools.convert(row.IoutADC,self.calib,Channel='CH1_R',BG=10,RG=3), axis=1)
            data['IoutAMAC']=data['IoutCalib']/G/0.008*1000
            data['eff']=(data.Iout/1000)*(data.Vout/1000)/(data.Iin-Ibase)/(data.Vin*10)

        self.dcdceff=data

    def render_iout(self):
        plt.plot(self.dcdceff.Iout,self.dcdceff.IoutADC)
        plt.xlabel('Iout [mA]')
        plt.ylabel('Iout [counts]')

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
