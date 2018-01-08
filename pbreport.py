import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import glob, re
import os.path

from IPython.display import HTML, display

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
        plt.semilogx(self.ileak.Ileak,self.ileak.OpAmpGain4,label='OpAmpGain3')
        plt.semilogx(self.ileak.Ileak,self.ileak.OpAmpGain8,label='OpAmpGain4')
        plt.xlabel('Ileak [V]')
        plt.ylabel('Ileak [counts]')
        plt.title(self.name)
        plt.legend(frameon=False)
