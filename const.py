HAAS_NUM_BOARD = 1
HAAS_RAM_WIDTH = 9 # width in bits of sample ram to use (e.g. 9==512 samples, 12(max)==4096 samples)
HAAS_MAX10ADCCHANS = []#[(0,110),(0,118),(1,110),(1,118)] #max10adc channels to draw (board, channel on board), channels: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp
HAAS_SENDINCREMENT=0 # 0 would skip 2**0=1 byte each time, i.e. send all bytes, 10 is good for lockin mode (sends just 4 samples)
HAAS_NUM_CHAN_PER_BOARD = 4 # number of high-speed adc channels on a haasoscope board
