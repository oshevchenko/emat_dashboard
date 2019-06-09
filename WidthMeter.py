from const import *
import numpy as np

class WidthMeter():
    def __init__(self):
        pass

    def freq(self,ydata,c1,downsample):
        tempc1=ydata[c1]
        mean_c1 = np.mean(tempc1)
        old_x = 0
        b = False
        cnt = 0
        first=True
        period=[]
        for x in range(len(tempc1)):
            if b and tempc1[x] > mean_c1:
                cnt = cnt+1
                if (cnt > 10):
                    cnt = 0
                    b = False
                    # print("x",x-old_x)
                    if not first:
                        period.append(x-old_x)
                    first=False
                    old_x=x
            if not b and tempc1[x] < mean_c1:
                cnt = cnt+1
                if (cnt > 10):
                    cnt = 0
                    b = True
            if b and tempc1[x] < mean_c1:
                cnt = 0
            if not b and tempc1[x] > mean_c1:
                cnt = 0
        mperiod = np.mean(period)
        F=1000*1000/(mperiod/(HAAS_CLKRATE/pow(2, downsample)))
        # print("F=",F)
        return F




