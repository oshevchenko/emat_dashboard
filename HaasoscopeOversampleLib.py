from const import *
import numpy as np

class HaasoscopeOversample():
    def __init__(self):
        self.dooversample=np.zeros(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is oversampling, 0 is no oversampling, 9 is over-oversampling

    def ToggleOversamp(self,chan):
        #tell it to toggle oversampling for this channel
        chanonboard = chan%HAAS_NUM_CHAN_PER_BOARD
        if chanonboard>1: return False
        if chanonboard==1 and self.dooversample[chan] and self.dooversample[chan-1]==9: print(("first disable over-oversampling on channel",chan-1)); return False
        # self.togglechannel(chan+2,True)
        self.dooversample[chan] = not self.dooversample[chan];
        print(("oversampling is now",self.dooversample[chan],"for channel",chan))
        return True
        # if self.dooversample[chan] and self.downsample>0: self.telldownsample(0) # must be in max sampling mode for oversampling to make sense
        # frame=[]
        # frame.append(141)
        # firmchan=self.getfirmchan(chan)
        # frame.append(firmchan)
        # self.ser.write(frame)
        # self.drawtext()
        # self.figure.canvas.draw()
    def oversample(self,ydata,c1,c2):
        tempc1=ydata[c1]
        tempc2=ydata[c2]
        adjustmeanandrms=True
        if adjustmeanandrms:
            mean_c1 = np.mean(tempc1)
            rms_c1 = np.sqrt(np.mean((tempc1-mean_c1)**2))
            mean_c2 = np.mean(tempc2)
            rms_c2 = np.sqrt(np.mean((tempc2-mean_c2)**2))
            meanmean=(mean_c1+mean_c2)/2.
            meanrms=(rms_c1+rms_c2)/2.
            tempc1=meanrms*(tempc1-mean_c1)/rms_c1 + meanmean
            tempc2=meanrms*(tempc2-mean_c2)/rms_c2 + meanmean
            # print (mean_c1, mean_c2, rms_c1, rms_c2)
        mergedsamps=np.empty(HAAS_NUM_SAMPLES*2)
        mergedsamps[0:HAAS_NUM_SAMPLES*2:2]=tempc1 # a little tricky which is 0 and which is 1 (i.e. which is sampled first!)
        mergedsamps[1:HAAS_NUM_SAMPLES*2:2]=tempc2
        ydata[c1]=mergedsamps[0:HAAS_NUM_SAMPLES]
        ydata[c2]=mergedsamps[HAAS_NUM_SAMPLES:HAAS_NUM_SAMPLES*2]


    def TryOversample(self,board,ydata):
        if self.dooversample[HAAS_NUM_CHAN_PER_BOARD*(HAAS_NUM_BOARD-board-1)]: self.oversample(ydata,0,2)
        if self.dooversample[HAAS_NUM_CHAN_PER_BOARD*(HAAS_NUM_BOARD-board-1)+1]: self.oversample(ydata,1,3)

    def overoversample(self,c1,c2):
        tempc1=np.concatenate([self.ydata[c1],self.ydata[c1+2]])
        tempc2=np.concatenate([self.ydata[c2],self.ydata[c2+2]])
        adjustmeanandrms=True
        if adjustmeanandrms:
            mean_c1 = np.mean(tempc1)
            rms_c1 = np.sqrt(np.mean((tempc1-mean_c1)**2))
            mean_c2 = np.mean(tempc2)
            rms_c2 = np.sqrt(np.mean((tempc2-mean_c2)**2))
            meanmean=(mean_c1+mean_c2)/2.
            meanrms=(rms_c1+rms_c2)/2.
            tempc1=meanrms*(tempc1-mean_c1)/rms_c1 + meanmean
            tempc2=meanrms*(tempc2-mean_c2)/rms_c2 + meanmean
            #print mean_c1, mean_c2, rms_c1, rms_c2
        ns=2*HAAS_NUM_SAMPLES
        mergedsamps=np.empty(ns*2)
        mergedsamps[0:ns*2:2]=tempc1 # a little tricky which is 0 and which is 1 (i.e. which is sampled first!)
        mergedsamps[1:ns*2:2]=tempc2
        self.ydata[c1]=mergedsamps[0:ns/2]
        self.ydata[c2]=mergedsamps[ns/2:ns]
        self.ydata[c1+2]=mergedsamps[ns:3*ns/2]
        self.ydata[c2+2]=mergedsamps[3*ns/2:ns*2]