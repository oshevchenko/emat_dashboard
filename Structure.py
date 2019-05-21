# Abstract struct class
class Structure:
    def __init__ (self, **argd):
        print((">>>>len(argd)",len(argd)))
        if len(argd):
            # Update by dictionary
            self.__dict__.update (argd)

# Specific class
class EmatGlobalStruct (Structure):

    def __init__ (self, *argv, **argd):
        super(EmatGlobalStruct, self).__init__(**argd)
        # Structure.__init__(self,argv,argd)

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
