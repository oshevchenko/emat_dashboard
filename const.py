HAAS_NUM_BOARD = 1
HAAS_RAM_WIDTH = 9 # width in bits of sample ram to use (e.g. 9==512 samples, 12(max)==4096 samples)
HAAS_MAX10ADCCHANS = []#[(0,110),(0,118),(1,110),(1,118)] #max10adc channels to draw (board, channel on board), channels: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp
HAAS_SENDINCREMENT=0 # 0 would skip 2**0=1 byte each time, i.e. send all bytes, 10 is good for lockin mode (sends just 4 samples)
HAAS_NUM_CHAN_PER_BOARD = 4 # number of high-speed adc channels on a haasoscope board
HAAS_NUM_SAMPLES = int(pow(2,HAAS_RAM_WIDTH)/pow(2,HAAS_SENDINCREMENT)) # num samples per channel, max is pow(2,ram_width)/pow(2,0)=4096
HAAS_NUM_BYTES = HAAS_NUM_SAMPLES*HAAS_NUM_CHAN_PER_BOARD #num bytes per board
HAAS_CLKRATE = 125.0
HAAS_NSAMP = pow(2,HAAS_RAM_WIDTH)-1 #samples for each max10 adc channel (4095 max (not sure why it's 1 less...))

MSG_ID_YDATA = 1
MSG_ID_DRAWTEXT = 2
MSG_ID_TOGGLE_LOGICANALYZER = 3
MSG_ID_SELECT_CHANNEL = 4
MSG_ID_SELECT_TRIGGER_CHANNEL = 5
MSG_ID_ADJUST = 6
MSG_ID_DOWNSAMPLE = 7
MSG_ID_TOGGLE_AUTO_REARM = 8
MSG_ID_TOGGLE_EXT_TRIG = 9
MSG_ID_TOGGLE_ROLL_TRIG = 10

DIR_DOWN = 0
DIR_UP = 1
DIR_RIGHT = 2
DIR_LEFT = 3



