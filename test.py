# pip install py-opc-ng pyusbiss pyserial

from time import sleep
from usbiss.spi import SPI
import opcng as opc

spi = SPI('COM3')
spi.mode = 1
spi.max_speed_hz = 500000
spi.lsbfirst = False

dev = opc.detect(spi)

print(f'device information: {dev.info()}')
print(f'serial: {dev.serial()}')
print(f'firmware version: {dev.serial()}')

# power on fan and laser
dev.on()

for i in range(10):
    # query particle mass readings
    sleep(1)
    print(dev.histogram())

# power off fan and laser
dev.off()

# Output Exmaple

# device information: OPC-N3 Iss1.1 FirmwareVer = 1.17a_02c.......................BS
# serial:  OPC-N3 177091518
# firmware version:  OPC-N3 177091518
# {'Bin 0': 0.0, 'Bin 1': 0.0, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0, 'Bin1 MToF': 0.0,
#     'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 22.82, 'SFR': 6.27, 'Temperature': 29.09094377050431, 'Relative humidity': 38.15365835049973, 'PM1': 0.0, 'PM2.5': 0.0, 'PM10': 0.0, '#RejectGlitch': 0, '#RejectLongTOF': 0, '#RejectRatio': 0, '#RejectOutOfRange': 0, 'Fan rev count': 0, 'Laser status': 584, 'Checksum': 60074}
# {'Bin 0': 7.704654895666131, 'Bin 1': 0.6420545746388443, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0, 'Bin1 MToF': 8.666666666666666,
#     'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.23, 'Temperature': 29.09094377050431, 'Relative humidity': 39.71923399710079, 'PM1': 0.5195785164833069, 'PM2.5': 0.53219074010849, 'PM10': 0.53219074010849, '#RejectGlitch': 1, '#RejectLongTOF': 0, '#RejectRatio': 6, '#RejectOutOfRange': 0, 'Fan rev count': 0, 'Laser status': 583, 'Checksum': 62536}
# {'Bin 0': 8.626198083067093, 'Bin 1': 0.9584664536741214, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0, 'Bin1 MToF': 8.0,
#     'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.26, 'Temperature': 29.077592126344697, 'Relative humidity': 39.78332188906691, 'PM1': 0.6147348880767822, 'PM2.5': 0.6315822005271912, 'PM10': 0.6315822005271912, '#RejectGlitch': 3, '#RejectLongTOF': 0, '#RejectRatio': 16, '#RejectOutOfRange': 0, 'Fan rev count': 0, 'Laser status': 583, 'Checksum': 15995}
# {'Bin 0': 10.50903119868637, 'Bin 1': 0.6568144499178982, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0, 'Bin1 MToF': 10.333333333333334,
#     'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.09, 'Temperature': 29.077592126344697, 'Relative humidity': 39.54985885404746, 'PM1': 0.6785355806350708, 'PM2.5': 0.6932470798492432, 'PM10': 0.6932470798492432, '#RejectGlitch': 7, '#RejectLongTOF': 0, '#RejectRatio': 9, '#RejectOutOfRange': 0, 'Fan rev count': 0, 'Laser status': 583, 'Checksum': 29525}
# {'Bin 0': 7.479674796747967, 'Bin 1': 0.6504065040650406, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.3252032520325203, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0, 'Bin1 MToF': 7.666666666666667,
#     'Bin3 MToF': 0.0, 'Bin5 MToF': 10.333333333333334, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.15, 'Temperature': 29.04821850919356, 'Relative humidity': 39.23247119859617, 'PM1': 0.6002933382987976, 'PM2.5': 2.022118330001831, 'PM10': 2.6402201652526855, '#RejectGlitch': 3, '#RejectLongTOF': 0, '#RejectRatio': 12, '#RejectOutOfRange': 1, 'Fan rev count': 0, 'Laser status': 583, 'Checksum': 61517}
# {'Bin 0': 13.893376413570273, 'Bin 1': 0.6462035541195477, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0, 'Bin1 MToF': 7.666666666666667,
#     'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.19, 'Temperature': 29.04821850919356, 'Relative humidity': 38.97154192416266, 'PM1': 0.8664505481719971, 'PM2.5': 0.8833721876144409, 'PM10': 0.8833721876144409, '#RejectGlitch': 1, '#RejectLongTOF': 0, '#RejectRatio': 14, '#RejectOutOfRange': 0, 'Fan rev count': 0, 'Laser status': 582, 'Checksum': 5613}
# {'Bin 0': 10.914927768860352, 'Bin 1': 0.32102728731942215, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0, 'Bin1 MToF': 7.333333333333333,
#     'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.23, 'Temperature': 29.034866865033948, 'Relative humidity': 38.79911497672999, 'PM1': 0.6549891829490662, 'PM2.5': 0.6661592721939087, 'PM10': 0.6661592721939087, '#RejectGlitch': 1, '#RejectLongTOF': 0, '#RejectRatio': 12, '#RejectOutOfRange': 2, 'Fan rev count': 0, 'Laser status': 582, 'Checksum': 7345}
# {'Bin 0': 7.961783439490445, 'Bin 1': 1.592356687898089, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0, 'Bin1 MToF': 8.0,
#     'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.28, 'Temperature': 29.034866865033948, 'Relative humidity': 38.65720607309071, 'PM1': 0.6648829579353333, 'PM2.5': 0.688485860824585, 'PM10': 0.688485860824585, '#RejectGlitch': 4, '#RejectLongTOF': 0, '#RejectRatio': 8, '#RejectOutOfRange': 3, 'Fan rev count': 0, 'Laser status': 581, 'Checksum': 6549}
# {'Bin 0': 8.346709470304976, 'Bin 1': 0.32102728731942215, 'Bin 2': 0.32102728731942215, 'Bin 3': 0.0, 'Bin 4': 0.0, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0,
#     'Bin1 MToF': 9.666666666666666, 'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.23, 'Temperature': 29.00549324788281, 'Relative humidity': 38.55039291981384, 'PM1': 0.6159453988075256, 'PM2.5': 0.6748248934745789, 'PM10': 0.6753007769584656, '#RejectGlitch': 2, '#RejectLongTOF': 0, '#RejectRatio': 8, '#RejectOutOfRange': 1, 'Fan rev count': 0, 'Laser status': 583, 'Checksum': 25260}
# {'Bin 0': 10.793650793650794, 'Bin 1': 1.2698412698412698, 'Bin 2': 0.0, 'Bin 3': 0.0, 'Bin 4': 0.31746031746031744, 'Bin 5': 0.0, 'Bin 6': 0.0, 'Bin 7': 0.0, 'Bin 8': 0.0, 'Bin 9': 0.0, 'Bin 10': 0.0, 'Bin 11': 0.0, 'Bin 12': 0.0, 'Bin 13': 0.0, 'Bin 14': 0.0, 'Bin 15': 0.0, 'Bin 16': 0.0, 'Bin 17': 0.0, 'Bin 18': 0.0, 'Bin 19': 0.0, 'Bin 20': 0.0, 'Bin 21': 0.0, 'Bin 22': 0.0, 'Bin 23': 0.0,
#     'Bin1 MToF': 7.666666666666667, 'Bin3 MToF': 0.0, 'Bin5 MToF': 0.0, 'Bin7 MToF': 0.0, 'Sampling Period': 0.5, 'SFR': 6.3, 'Temperature': 29.034866865033948, 'Relative humidity': 38.51377126726177, 'PM1': 0.918687105178833, 'PM2.5': 1.5940775871276855, 'PM10': 1.6857167482376099, '#RejectGlitch': 4, '#RejectLongTOF': 0, '#RejectRatio': 13, '#RejectOutOfRange': 0, 'Fan rev count': 0, 'Laser status': 583, 'Checksum': 8107}
