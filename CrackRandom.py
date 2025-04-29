from sage.all import *
import logging
from colorama import Fore, Style, init
from random import Random, getrandbits

# 初始化 colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }
    NAME_COLOR = Fore.MAGENTA  # logger 名称的颜色
    MESSAGE_COLOR = Fore.WHITE  # 消息的颜色
    TIME_COLOR = Fore.GREEN  # 时间戳的颜色

    def format(self, record):
        level_color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        levelname = level_color + record.levelname + Style.RESET_ALL
        # 设置 logger 名称颜色
        name = self.NAME_COLOR + record.name + Style.RESET_ALL
        # 设置消息颜色
        message = self.MESSAGE_COLOR + record.getMessage() + Style.RESET_ALL
        # 设置时间戳颜色
        asctime = self.TIME_COLOR + self.formatTime(record, self.datefmt) + Style.RESET_ALL
        # 格式化日志
        return f"{asctime} [{levelname}] {name} | {message}"

class CrackRandom:
    """
    Copyright (C) 2025 WuYan.
    """
    def __init__(self, loglevel:str="INFO"):
        """
        Choose loglevel in ["DEBUG","INFO","WARNING","ERROR"].
        """
        self.L = []
        self.R = []
        self.bits = []
        self.totalbitsize = 0
        self.logger = self._setLog(loglevel)
        self.logger.debug("Init done.")
    
    def _setLog(self, loglevel:str):
        logger = logging.getLogger("CrackRandom")
        logger.setLevel(loglevel)
        handler = logging.StreamHandler()
        handler.setLevel(loglevel)
        formatter = ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def _checkSufficient(self) -> bool:
        if self.totalbitsize < 19968:
            self.logger.info(f"The bits is not enough to crack MT19937. Now got {self.totalbitsize} bits.")
            return False
        return True
    
    def _constructRow(self, RNG:Random) -> list:
        row = []
        for bitsize,bitvalue,known in self.bits:
            if known:
                row += [int(i) for i in bin(RNG.getrandbits(bitsize))[2:].zfill(bitsize)]
            else:
                RNG.getrandbits(bitsize)
        return row
    
    def _checkState(self, state:list) -> bool:
        RNG = Random()
        RNG.setstate((3,tuple(state+[624]),None))
        for idx,value in enumerate(self.bits):
            bitsize,bitvalue,known = value
            predict = RNG.getrandbits(bitsize)
            if known:
                if predict!=bitvalue:
                    self.logger.error(f"No.{idx}: Bitsize({bitsize}) ExpectedValue({bitvalue}) PredictValue({predict}) Unmatch")
                    return False
                else:
                    self.logger.debug(f"No.{idx}: Bitsize({bitsize}) ExpectedValue({bitvalue}) PredictValue({predict}) Match")
            else:
                self.logger.debug(f"No.{idx}: UnknownBit Bitsize({bitsize}) PredictValue({predict})")
                RNG.getrandbits(bitvalue)
        return True                


    def uploadValues(self, bitsize:int, bitvalue:int, known:bool=True):
        """
        If the random number generator has generated some random numbers in the middle that you don't know, but you know the bitsize, it can also be cracked. You can use "known=False" to add them.
        """
        if bitvalue >= (1<<bitsize):
            self.logger.error(f"Your bitvalue is greater than the max number of your bitsize.")
            return
        self.bits.append([bitsize, bitvalue, known])
        if known:
            self.totalbitsize += bitsize
            self.R += [int(i) for i in bin(bitvalue)[2:].zfill(bitsize)]
            self.logger.debug(f"Already got {self.totalbitsize} bits.")

    def randomPredict(self) -> Random:
        """
        Bomb!!!
        """
        if self._checkSufficient():
            self.logger.info("Start constructing the matrix. It will take a few minutes.")
            # divide into two parts to avoid storing too much data in memory. (Will be killed in 8GB memory if not to do so)
            for i in range(19968):        # You can use tqdm.trange() to see the exact time.
                state = [0]*624
                temp = "0"*i + "1"*1 + "0"*(19968-1-i)
                for j in range(624):
                    state[j] = int(temp[32*j:32*j+32], 2)
                RNG = Random()
                RNG.setstate((3,tuple(state+[624]),None))
                self.L.append(self._constructRow(RNG))
                if i==9983:
                    L1 = Matrix(GF(2), self.L)
                    self.L.clear()
                    self.logger.info("Half done.")
            L2 = Matrix(GF(2), self.L)
            L = L1.stack(L2)
            R = vector(GF(2), self.R)
            self.logger.info("Matrix init done.")
            matrix_rank = L.rank()
            self.logger.debug(f"Matrix rank is {matrix_rank}.")
            if matrix_rank < 19937:
                self.logger.warning("Maybe there will be multiple solutions and fail to predict. Try to add more bits.")
            self.logger.info("Start solving...")
            try:
                s = L.solve_left(R)
            except:
                self.logger.error("Can't find the solution. Check your data.")
                return None
            init = "".join(list(map(str,s)))
            state = []
            for i in range(624):
                state.append(int(init[32*i:32*i+32],2))
            if self._checkState(state):
                self.logger.info("Successfully solved with check.")
                RNG = Random()
                RNG.setstate((3,tuple(state+[624]),None))
                return RNG
            else:
                self.logger.error("Unsuccessfully solved. Unable to pass the check.")
        return None
        
    
if __name__ == "__main__":
    crack = CrackRandom()
    length = 8
    times = 19968//length
    for i in range(times):
        crack.uploadValues(length,getrandbits(length))
    RNG = crack.randomPredict()
    for i in range(times):
        RNG.getrandbits(length)
    print(RNG.getrandbits(length),getrandbits(length))

    # crack = CrackRandom("DEBUG")
    # bitlenths = [1,44,63,22]*(19968//64)
    # assert 19968==sum(bitlenths[::2])
    # for i in range(len(bitlenths)):
    #     if i%2==0:
    #         crack.uploadValues(bitlenths[i],getrandbits(bitlenths[i]),True)
    #     else:
    #         getrandbits(bitlenths[i])   #left unknown
    #         crack.uploadValues(bitlenths[i],0,False)
    # RNG = crack.randomPredict()

    # crack = CrackRandom()
    # length = 12
    # times = 19968//length+500   # need more to make sure the matrix's rank is 19937
    # for i in range(times):
    #     crack.uploadValues(length,getrandbits(length))
    # RNG = crack.randomPredict()
    # for i in range(times):
    #     RNG.getrandbits(length)
    # print(RNG.getrandbits(length),getrandbits(length))