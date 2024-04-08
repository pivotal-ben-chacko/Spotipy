# Seengreat RC522 RFID HAT control demo
# Author(s):Andy Li from Seengreat
# This demo is used for spi interface
# Describe:Write 16 bytes of content to block 8 of the S50 card and then read the UID of the card and the content of block 8 in a loop
# Hardware Connection :
#	SW1:   RX   -> OFF			SW2:	A1	 -> -
#          TX   -> OFF					A0	 -> +
#          SDA  -> OFF					ADR5 -> 0
#          SCL  -> OFF					ADR4 -> 0
#          NSS  -> ON					ADR3 -> 0
#          MOSI -> ON					ADR2 -> 0
#          MISO -> ON					ADR1 -> 0
#          SCK  -> ON					ADR0 -> 0

import serial
import time
import numpy as np
import wiringpi
import spidev

# the M1 card is divided into 16 sectors, each sector consists of four blocks(block0,block1,block2,block3)
# the 64 blocks of 16 sectors are numbered by absolute address:0~63
# block 0 of 0th sector(ie absolute address 0 block) is used to store the manufacturer code,which has been
# cured and cannot be changed
# block 0,block 1, and block 2 of each sector are data blocks,which can be used to store data
# block 3 of each sector is a control block (absolute address:block 3,block 7,block 11...) including
# password A,access control,password B,etc

#MF522 command
PCD_IDLE              = 0x00    #cancel the current command
PCD_CALCCRC           = 0x03    #CRC calculate
PCD_TRANSMIT          = 0x04    #send data
PCD_RECEIVE           = 0x08    #receive data
PCD_TRANSCEIVE        = 0x0C    #send and receive data
PCD_AUTHENT           = 0x0E    #authenticate key
PCD_RESETPHASE        = 0x0F    #reset
#Mifare_One card command
PICC_REQIDL           = 0x26    #search cards that are not sleeping within the antenna
PICC_REQALL           = 0x52    #search all cards in the antenna
PICC_ANTICOLL1        = 0x93    #anti-collision
PICC_ANTICOLL2        = 0x95    #anti-collision
PICC_AUTHENT1A        = 0x60    #authenticate A key
PICC_AUTHENT1B        = 0x61    #authenticate B key
PICC_READ             = 0x30    #read block
PICC_WRITE            = 0xA0    #write block
PICC_DECREMENT        = 0xC0    #decrease payment
PICC_INCREMENT        = 0xC1    #increase payment
PICC_RESTORE          = 0xC2    #store block data to FIFO
PICC_TRANSFER         = 0xB0    #save FIFO data
PICC_HALT             = 0x50    #dormancy
#MF522 FIFO length
DEF_FIFO_LENGTH       = 64      #FIFO size=64byte
MAXRLEN  = 18
#MF522 regsiter
# PAGE 0
RFU00                 = 0x00
CommandReg            = 0x01
ComIEnReg             = 0x02
DivlEnReg             = 0x03
ComIrqReg             = 0x04
DivIrqReg             = 0x05
ErrorReg              = 0x06
Status1Reg            = 0x07
Status2Reg            = 0x08
FIFODataReg           = 0x09
FIFOLevelReg          = 0x0A
WaterLevelReg         = 0x0B
ControlReg            = 0x0C
BitFramingReg         = 0x0D
CollReg               = 0x0E
RFU0F                 = 0x0F
# PAGE 1
RFU10                 = 0x10
ModeReg               = 0x11
TxModeReg             = 0x12
RxModeReg             = 0x13
TxControlReg          = 0x14
TxAutoReg             = 0x15
TxSelReg              = 0x16
RxSelReg              = 0x17
RxThresholdReg        = 0x18
DemodReg              = 0x19
RFU1A                 = 0x1A
RFU1B                 = 0x1B
MifareReg             = 0x1C
RFU1D                 = 0x1D
RFU1E                 = 0x1E
SerialSpeedReg        = 0x1F
# PAGE 2
RFU20                 = 0x20
CRCResultRegM         = 0x21
CRCResultRegL         = 0x22
RFU23                 = 0x23
ModWidthReg           = 0x24
RFU25                 = 0x25
RFCfgReg              = 0x26
GsNReg                = 0x27
CWGsCfgReg            = 0x28
ModGsCfgReg           = 0x29
TModeReg              = 0x2A
TPrescalerReg         = 0x2B
TReloadRegH           = 0x2C
TReloadRegL           = 0x2D
TCounterValueRegH     = 0x2E
TCounterValueRegL     = 0x2F
# PAGE 3
RFU30                 = 0x30
TestSel1Reg           = 0x31
TestSel2Reg           = 0x32
TestPinEnReg          = 0x33
TestPinValueReg       = 0x34
TestBusReg            = 0x35
AutoTestReg           = 0x36
VersionReg            = 0x37
AnalogTestReg         = 0x38
TestDAC1Reg           = 0x39
TestDAC2Reg           = 0x3A
TestADCReg            = 0x3B
RFU3C                 = 0x3C
RFU3D                 = 0x3D
RFU3E                 = 0x3E
RFU3F                 = 0x3F

#MF522 errno
MI_OK                 = 0
MI_NOTAGERR           = 1
MI_ERR                = 2
#SHAQU1                = 0x01
#KUAI4                 = 0x04
#KUAI7                 = 0x07
#REGCARD               = 0xa1
#CONSUME               = 0xa2
READCARD              = 0xa3
ADDMONEY              = 0xa4


class Rc522_api(object):
    def __init__(self):
        self.CT = [0, 0]  # card type
        self.SN = [0, 0, 0, 0]  # card serial number
        self.RFID = [0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0]  # RFID
        self.total = 0
        self.KEY = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
        self.AUDIO_OPEN = [0xAA, 0x07, 0x02, 0x00, 0x09, 0xBC]
        self.RFID1 = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x07, 0x80, 0x29, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
        self.card_id = [0,0,0,0,0,0,0,0,
                        0,0,0,0,0,0,0,0]
        self.status = 0
        self.block_num = 0x08
        self.bus = 0
        self.dev = 0
        self.spi_speed = 1000000
        self.spi = spidev.SpiDev()
        self.spi.open(self.bus, self.dev)
        self.spi.max_speed_hz = self.spi_speed
        self.spi.mode = 0b00
        self.spi.xfer([1000000, 10, 8])

        print('spi init')
        wiringpi.wiringPiSetup()
        wiringpi.pinMode(24, 1)  # buzzer pin
        wiringpi.pinMode(25, 1)  # reset pin
        wiringpi.pinMode(29, 1)  # led pin
        wiringpi.digitalWrite(29,1)  # turn off red led

    def write_rawrc(self, ucaddress, ucvalue):
        """"write rc522 register"""
        addr = (ucaddress << 1) & 0x7E
        self.spi.writebytes([addr,ucvalue])  #register addr(the lowest 6 bits are the actual address，MSB:1)

    def read_rawrc(self, ucaddress):
        """read current value from the register"""
        addr = ((ucaddress <<1) & 0x7E) | 0x80
        self.spi.writebytes([addr])
        res = self.spi.readbytes(1)
        return int.from_bytes(res, 'little')

    def clear_bitmask(self, ucreg, ucmask):
        """clear_bitmask clear RC522 register bit"""
        uctemp = self.read_rawrc(ucreg)
        self.write_rawrc(ucreg, uctemp & (~ ucmask))  # clear bit mask

    def set_bitmask(self, ucreg, ucmask):
        """set_bitmask set bit for RC522 register"""
        uctemp = self.read_rawrc(ucreg)
        self.write_rawrc(ucreg, uctemp | ucmask)  # set bit mask

    def pcd_antenna_on(self):
        """pcd_antenna_on :turn on the antenna"""
        uc = self.read_rawrc(TxControlReg)
        if (uc & 0x03) == 0:
            self.set_bitmask(TxControlReg, 0x03)

    def pcd_antenna_off (self):
        """pcd_antenna_off turn off the antenna """
        self.clear_bitmask(TxControlReg, 0x03)

    def pcd_config_iso_type(self, uctype):
        """set RC522 work mode"""
        if uctype == 'A':  # ISO14443_A
            self.clear_bitmask(Status2Reg, 0x08)
            self.write_rawrc(ModeReg, 0x3D)  # 3F
            self.write_rawrc(RxSelReg, 0x86)  # 84
            self.write_rawrc(RFCfgReg, 0x7F)  # 4F
            self.write_rawrc(TReloadRegL, 30)  # tmoLength) # TReloadVal = 'h6a =tmoLength(dec)
            self.write_rawrc(TReloadRegH, 0)
            self.write_rawrc(TModeReg, 0x8D)
            self.write_rawrc(TPrescalerReg, 0x3E)
            time.sleep(0.001)
            self.pcd_antenna_on()  # turn antenna

    def pcd_com_mf522(self, uccommand, pindata, ucinlenbyte, poutdata):
        """communication between RC522 and ISO14443 card
           uccommand，RC522 command
           pindata，the data from RC522 send to the card
           ucinlenbyte，len for data send
           poutdata，data received
           return : status MI_OK，sucess
        """
        cstatus = MI_ERR
        ucirqen = 0x00
        ucwaitfor = 0x00
        uclastbits = 0
        poutlenbit = 0
        ucn = 0
        ul = 0
        if uccommand == PCD_AUTHENT:  # Mifare authenticate
            ucirqen = 0x12  # error interrupt request enabled:ErrIEn IdleIEn
            ucwaitfor = 0x10  # time for Request and authenticate and check the idleIRq bit
        elif uccommand == PCD_TRANSCEIVE:  # receive and send
            ucirqen = 0x77  # enable TxIEn RxIEn IdleIEn LoAlertIEn ErrIEn TimerIEn
            ucwaitfor = 0x30  # time for Request and authenticate and check the RxIRq IdleIRq bit

        self.write_rawrc(ComIEnReg, ucirqen | 0x80)  # IRqInv sets the pin IRQ to the opposite
                                                    #value of the IRq bit of Status1Reg
        self.clear_bitmask(ComIrqReg, 0x80)  # when Set1 bit were cleared，clear CommIRqReg mask bit
        self.write_rawrc(CommandReg, PCD_IDLE)  # write IDLE command
        self.set_bitmask(FIFOLevelReg, 0x80)  # set FlushBuffer to clear the read and write pointers of
                                             # the internal FIFO and the BufferOvfl flag of ErrReg is cleared

        for i in range(ucinlenbyte):
            data = int.from_bytes(pindata[i], 'little')
            self.write_rawrc(FIFODataReg, data)  # write data to FIFO
        self.write_rawrc(CommandReg, uccommand)  # write command

        if uccommand == PCD_TRANSCEIVE:
            self.set_bitmask(BitFramingReg, 0x80)  # StartSend is set to start data transmission. The bit
                                                  #is only valid when used with send and receive commands

        ul = 1000  # adjusted according to the clock frequency, the maximum
                   # waiting time for operating the M1 card is 25 ms
        while ul > 0:
            ucn = self.read_rawrc(ComIrqReg)
            ul -= 1
            if (ucn & 0x01) > 0 or (ucn & ucwaitfor) > 0:  # check event interrupt
                break
        self.clear_bitmask(BitFramingReg, 0x80)  # clear StartSend bit
        if ul != 0:
            if not(self.read_rawrc(ErrorReg) & 0x1B):  # read error flag:register BufferOfI CollErr ParityErr ProtocolErr
                cstatus = MI_OK
                if (ucn & ucirqen & 0x01):  # time interrupt occurs
                    cstatus = MI_NOTAGERR
                if uccommand == PCD_TRANSCEIVE:
                    ucn = self.read_rawrc(FIFOLevelReg)  # read len from FIFO save data
                    uclastbits = self.read_rawrc(ControlReg) & 0x07  # the number of valid bits of the last received byte
                    if (uclastbits):
                        poutlenbit = (ucn - 1) * 8 + uclastbits  # N bytes minus 1 (the last byte) + the number
                                                                 # of valid bits of the last received byte
                    else:
                        poutlenbit = ucn * 8  # last received byte whole byte valid
                    if ucn == 0:
                        ucn = 1
                    if ucn > MAXRLEN:
                        ucn = MAXRLEN
                    ul = 0
                    for ul in range(ucn):
                        poutdata[ul] = self.read_rawrc(FIFODataReg)
            else:
                cstatus = MI_ERR
        self.set_bitmask(ControlReg, 0x80)  # stop timer now
        self.write_rawrc(CommandReg, PCD_IDLE)
        return cstatus, poutlenbit

    def read(self, block_number):
        """user read block data"""
        status = self.pcd_request(PICC_REQALL)  # Request card
        if status == MI_OK:  # Request success
            status = MI_ERR
            status = self.pcd_anticoll()  # Anticoll
        if status == MI_OK:  # Anticoll success
            status = MI_ERR
            status = self.pcd_select()
        if status == MI_OK:  # select card success
            status = MI_ERR
            status = self.pcd_authstate(0x60, 0x09)
        if status == MI_OK:  # AuthState success
            status = MI_ERR
            status = self.pcd_read(block_number)
        if status == MI_OK:  # read card success
            status = MI_ERR
            for i in range(16):
                self.card_id[i] = self.RFID[i]  # get RFID
            return True
        return False

    def write(self, block_number, data):
        """user write data to block"""
        if data == None:
            return False
        status = self.pcd_request(PICC_REQALL)  # Request card
        if status == MI_OK:  # Request success
            status = MI_ERR
            status = self.pcd_anticoll()  # Anticoll
        if status == MI_OK:  # Anticoll success
            status = MI_ERR
            status = self.pcd_select()
        if status == MI_OK:  # select card success
            status = MI_ERR
            status = self.pcd_authstate(0x60, 0x09)
        if status == MI_OK:  # AuthState success
            status = MI_ERR
            status = self.pcd_write(block_number, data)
        if status == MI_OK:  # write card success
            print('write sucess')
            return True
        return False

    def pcd_request(self, ucreq_code):
        """input  ：ucReq_code，Request card mode
           = 0x52，find all 14443A-compliant cards in the induction area
           = 0x26，find a card that is not in sleep mode
             pTagType，card type
           = 0x4400，Mifare_UltraLight
           = 0x0400，Mifare_One(S50)
           = 0x0200，Mifare_One(S70)
           = 0x0800，Mifare_Pro(X))
           = 0x4403，Mifare_DESFire
          return: status MI_OK，sucess"""
        cstatus = 0
        uccommf522buf = np.arange(0, MAXRLEN, 1)
        ullen = 0
        self.clear_bitmask(Status2Reg, 0x08)  # clear up the case in which the MIFARECyptol unit was
                                             # turned on and all card data communications were encrypted
        self.write_rawrc(BitFramingReg, 0x07) # send the seven bits of the last byte
        self.set_bitmask(TxControlReg, 0x03)  # the output signal of the TX1, TX2 pin transmits
                                             # the modulated 13.56 energy carrier signal
        uccommf522buf[0] = ucreq_code  # store card commmand word
        cstatus, ullen = self.pcd_com_mf522(PCD_TRANSCEIVE, uccommf522buf, 1, uccommf522buf)  # Request
        if (cstatus == MI_OK) and (ullen == 0x10):  #Request success return card type
            self.CT = uccommf522buf[0:2]
        else:
            cstatus = MI_ERR
        return cstatus

    def pcd_anticoll(self):
        """card anticoll
        get 4 bytes of card serial number
        """
        uc = 0
        ucSnr_check = 0
        uccommf522buf = np.arange(0, MAXRLEN, 1)
        ullen = 0
        self.clear_bitmask(Status2Reg, 0x08)  # clear the MFCryptol On bit This bit can only be set
                                             # after a successful MFAuthent command is executed
        self.write_rawrc(BitFramingReg, 0x00)  # clear register  stop send and
        self.clear_bitmask(CollReg, 0x80)  # clear ValuesAfterColl all received bits are cleared after collision
        uccommf522buf[0:2] = 0x93, 0x20  # Anticoll command
        cstatus, ullen = self.pcd_com_mf522(PCD_TRANSCEIVE, uccommf522buf, 2, uccommf522buf)  # communicate to the card
        if cstatus == MI_OK:  #communition
            for uc in range(4):
                self.SN[uc] = uccommf522buf[uc]  #read UID
                ucSnr_check ^= uccommf522buf[uc]
            if ucSnr_check != uccommf522buf[uc+1]:
                cstatus = MI_ERR

        self.set_bitmask(CollReg, 0x80)
        return cstatus

    def calulate_crc(self, pindata, uclen):
        """alculate CRC16 with RC522"""
        self.clear_bitmask(DivIrqReg, 0x04)
        self.write_rawrc(CommandReg, PCD_IDLE)
        self.set_bitmask(FIFOLevelReg, 0x80)

        for uc in range(uclen):
            data = int.from_bytes(pindata[uc], 'little')
            self.write_rawrc(FIFODataReg, data)
        self.write_rawrc(CommandReg, PCD_CALCCRC)
        uc = 0xFF
        while uc > 0:
            ucn = self.read_rawrc(DivIrqReg)
            uc -= 1
            if (ucn & 0x04) > 0:
                break
        res_l = self.read_rawrc(CRCResultRegL)
        res_m = self.read_rawrc(CRCResultRegM)

        return res_l, res_m

    def pcd_select(self):
        """select card
        card serial number is 4 bytes
        """
        uccommf522buf = np.arange(0, MAXRLEN, 1)
        uccommf522buf[0] = PICC_ANTICOLL1
        uccommf522buf[1] = 0x70
        uccommf522buf[6] = 0
        for uc in range(4):
            uccommf522buf[uc + 2] = self.SN[uc]
            uccommf522buf[6] ^= self.SN[uc]

        uccommf522buf[7], uccommf522buf[8] = self.calulate_crc(uccommf522buf, 7)

        self.clear_bitmask(Status2Reg, 0x08)

        ucn, ullen = self.pcd_com_mf522(PCD_TRANSCEIVE, uccommf522buf, 9, uccommf522buf)
        if (ucn == MI_OK) and (ullen == 0x18):
            ucn = MI_OK
        else:
            ucn = MI_ERR

        return ucn

    def pcd_authstate(self, ucauth_mode, ucaddr):
        """authenticate card key
        key authenticate mode = 0x60，authenticate A key
                              = 0x61，authenticate B key
        ucaddr is block addr
        """
        uccommf522buf = np.arange(0, MAXRLEN, 1)
        ullen = 0
        uccommf522buf[0:2] = ucauth_mode, ucaddr
        uccommf522buf[2:8] = self.KEY
        uccommf522buf[8:12] = self.SN

        cstatus, ullen = self.pcd_com_mf522(PCD_AUTHENT, uccommf522buf, 12, uccommf522buf)
        if (cstatus != MI_OK) or (not(self.read_rawrc(Status2Reg) & 0x08)):
            cstatus = MI_ERR
        return cstatus

    def pcd_write(self, block_number, pdata):
        """write data to block of M1 card
        data length is 16 bytes
        """
        uccommf522buf = np.arange(0, MAXRLEN, 1)
        ullen = 0
        uccommf522buf[0:2] = PICC_WRITE, block_number
        uccommf522buf[2], uccommf522buf[3] = self.calulate_crc(uccommf522buf, 2)
        cstatus, ullen = self.pcd_com_mf522(PCD_TRANSCEIVE, uccommf522buf, 4, uccommf522buf)
        if (cstatus != MI_OK) or (ullen != 4) or ((uccommf522buf[0] & 0x0F) != 0x0A):
            cstatus = MI_ERR
        if cstatus == MI_OK:
            uc = 0
            for uc in range(len(pdata)):
                uccommf522buf[uc] = pdata[uc]
            uccommf522buf[16], uccommf522buf[17] = self.calulate_crc(uccommf522buf, 16)
            cstatus, ullen= self.pcd_com_mf522(PCD_TRANSCEIVE, uccommf522buf, 18, uccommf522buf)
            if (cstatus != MI_OK) or (ullen != 4) or ((uccommf522buf[0] & 0x0F) != 0x0A):
                cstatus = MI_ERR
        return cstatus

    def pcd_read(self, block_number):
        """read block data from M1 card
        data length is 16 bytes
        """
        uccommf522buf = np.arange(0, MAXRLEN, 1)
        ullen = 0
        uccommf522buf[0:2] = PICC_READ, block_number
        uccommf522buf[2], uccommf522buf[3] = self.calulate_crc(uccommf522buf, 2)
        cstatus, ullen = self.pcd_com_mf522(PCD_TRANSCEIVE, uccommf522buf, 4, uccommf522buf)

        if (cstatus == MI_OK) and (ullen == 0x90):
            self.RFID = uccommf522buf[0:16]
        else:
            cstatus = MI_ERR
        return cstatus

    def pcd_reset(self):
        """rc522 reset"""
        wiringpi.digitalWrite(25,0)
        time.sleep(0.001)
        wiringpi.digitalWrite(25,1)
        time.sleep(0.001)
        self.write_rawrc(CommandReg, PCD_RESETPHASE)  # reset the rc522

        while True:
            temp = self.read_rawrc(CommandReg)
            if (temp & 0x10) == 0:
                print('OK')
                break
        self.read_rawrc(CommandReg)
        time.sleep(0.001)
        self.write_rawrc(ModeReg, 0x3D)  # define the common mode of sending and receiving,
                                        # communicate with Mifare card,the initial value of CRC is 0x6363
        self.write_rawrc(TReloadRegL, 30)  # low bit for 16-bit timer
        self.write_rawrc(TReloadRegH, 0)  # high bit for 16-bit timer
        self.write_rawrc(TModeReg, 0x8D)  # define the settings for the internal timer
        self.write_rawrc(TPrescalerReg, 0x3E)  # set the timer division factor
        self.write_rawrc(TxAutoReg, 0x40)  # the modulated transmit signal set to 100%ASK

    def init(self):
        """rc522 init"""
        time.sleep(1)
        self.pcd_reset()
        self.pcd_config_iso_type('A')  # set work mode
