# Abstract struct class
class Structure:
    def __init__ (self, **argd):
        print((">>>>len(argd)",len(argd)))
        if len(argd):
            # Update by dictionary
            self.__dict__.update (argd)

# Specific class
class EmatGlobalStruct (Structure):
    num_board = 1 # Number of Haasoscope boards to read out
    ram_width = 9 # width in bits of sample ram to use (e.g. 9==512 samples, 12(max)==4096 samples)
    max10adcchans=[]#[(0,110),(0,118),(1,110),(1,118)] #max10adc channels to draw (board, channel on board), channels: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp
    sendincrement=0 # 0 would skip 2**0=1 byte each time, i.e. send all bytes, 10 is good for lockin mode (sends just 4 samples)
    num_chan_per_board = 4 # number of high-speed ADC channels on a Haasoscope board

    def __init__ (self, *argv, **argd):
        super(EmatGlobalStruct, self).__init__(**argd)
        # Structure.__init__(self,argv,argd)
        self.num_samples = int(pow(2,self.ram_width)/pow(2,self.sendincrement)) # num samples per channel, max is pow(2,ram_width)/pow(2,0)=4096

    def testBit(self,int_type, offset):
        mask = 1 << offset
        return(int_type & mask)
    # setBit() returns an integer with the bit at 'offset' set to 1.
    def setBit(self,int_type, offset):
        mask = 1 << offset
        return(int_type | mask)
    # clearBit() returns an integer with the bit at 'offset' cleared.
    def clearBit(self,int_type, offset):
        mask = ~(1 << offset)
        return(int_type & mask)
    # toggleBit() returns an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0.
    def toggleBit(self,int_type, offset):
        mask = 1 << offset
        return(int_type ^ mask)
