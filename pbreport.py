import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import glob, re
import os.path

from IPython.display import HTML, display

class Reports:
    def __init__(self,reports):
        self.names   =[r.name for r in reports]

        self.vin=pd.concat([r.vin for r in reports], ignore_index=True) if len(reports)>0 else None
        self.ileak=pd.concat([r.ileak for r in reports], ignore_index=True) if len(reports)>0 else None

    def append(self,r):
        self.names.append(r.name)

        self.vin=pd.concat([r.vin, self.vin], ignore_index=True) if self.vin is not None else r.vin
        self.ileak=pd.concat([r.ileak, self.ileak], ignore_index=True) if self.ileak is not None else r.ileak


class Report:
    def __init__(self,name):
        self.name=name
        self.vin=None
        self.ileak=None

        self.load_vin()
        self.load_ileak()

    def load_vin(self):
        datapath='pblog/{PB}_VIN.log'.format(PB=self.name)
        data=pd.DataFrame()
        if os.path.exists(datapath):
            data=pd.read_csv(datapath,sep=' ')
            data['PB']=self.name
        self.vin=data

    def render_vin(self):
        plt.plot(self.vin.Vin,self.vin.VinADC)
        plt.xlabel('Vin [V]')
        plt.ylabel('Vin [counts]')

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
