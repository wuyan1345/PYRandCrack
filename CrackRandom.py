from sage.all import *
import logging
from colorama import Fore, Style, init
import random
import os
import hashlib

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
        self.T = 19968
        self.L = []
        self.R = []
        self.blocks = []
        self.bits = []
        self.state = []
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
    
    def _checkSufficient(self):
        matrix_rank = self.L.rank()
        self.logger.info(f"Matrix rank is {matrix_rank}.")
        if matrix_rank < 19937:
            self.logger.warning("Maybe there will be multiple solutions and fail to predict. Try to add more bits.")
    
    def _constructRow(self, RNG:random.Random) -> list:
        row = []
        for bitsize,bitvalue,known in self.bits:
            if known:
                row += [int(i) for i in bin(RNG.getrandbits(bitsize))[2:].zfill(bitsize)]
            else:
                RNG.getrandbits(bitsize)
        return row
    
    def _constructMatrixBlock(self, start:int, end:int) -> Matrix:
        block = []
        for i in range(start,end):      # You can use tqdm.trange() to see the exact time.
            state = [0]*624
            temp = "0"*i + "1"*1 + "0"*(self.T-1-i)
            for j in range(624):
                state[j] = int(temp[32*j:32*j+32], 2)
            RNG = random.Random()
            RNG.setstate((3,tuple(state+[624]),None))
            block.append(self._constructRow(RNG))
        return Matrix(GF(2), block)
    
    def _checkState(self, state:list) -> bool:
        RNG = random.Random()
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
    
    def _findMinPeriod(self, lst:list) -> int:
        n = len(lst)
        for p in range(1, n + 1):
            if all(lst[i] == lst[i % p] for i in range(n)):
                return p
        return n
    
    def _mySeed(self, key:list) -> int:
        mySeed = 0
        for i in range(len(key)-1,-1,-1):
            mySeed = mySeed << 32
            mySeed += key[i]-i
        return mySeed

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

    def randomPredict(self) -> random.Random:
        """
        Bomb!!!
        """
        self.logger.info("Start constructing the matrix. It will take a few minutes.")
        # divide into several parts to avoid storing too much data in memory. (Will be killed in 8GB memory if not to do so)
        num = 4
        chunk_size = self.T//num if self.T %num==0 else self.T//num + 1
        indices = []
        for i in range(num):
            start = i * chunk_size
            end = min((i + 1) * chunk_size, self.T)
            if start < self.T:
                indices.append((start, end))

        self.blocks = []
        for i,(start,end) in enumerate(indices):
            self.logger.info(f"Constructing block {i+1}/{num}...")
            self.blocks.append(self._constructMatrixBlock(start, end))
        
        self.L = self.blocks[0]
        for i in range(1, len(self.blocks)):
            self.L = self.L.stack(self.blocks[i])

        R = vector(GF(2), self.R)
        self.logger.info("Matrix init done.")
        self._checkSufficient()
        self.logger.info("Start solving...")
        try:
            s = self.L.solve_left(R)
        except:
            self.logger.error("Can't find the solution. Check your data.")
            return None
        init = "".join(list(map(str,s)))
        state = []
        for i in range(624):
            state.append(int(init[32*i:32*i+32],2))
        if self._checkState(state):
            self.logger.info("Successfully solved with check.")
            self.state = state[:]
            RNG = random.Random()
            RNG.setstate((3,tuple(self.state+[624]),None))
            return RNG
        else:
            self.logger.error("Unsuccessfully solved. Unable to pass the check.")
            return None
    
    def getSeed(self, smallseed:bool=False, keylen:int=624, lower:int=None):
        """
        Guess the seed with the state.
        """
        # if you want to get a smallseed, let smallseed=True && keylen=624
        if smallseed and (keylen != 624 or lower is not None):
            self.logger.error("If you really need a small seed, implement your own logic to find one or just let keylen=624 and lower=None.")
            return
        if self.state == []:
            self.logger.error("Please pass the randomPredict first.")
            return
        N = 624
        uint32_mask = 1 << 32
        state = list(self.state)
        assert len(state) == N
        if state[0] != 0x80000000:
            self.logger.error("The state is invalid.")
            return
        
        step1_rnd = max(624, keylen)
        state[0] = state[N-1]
        i = (1 + step1_rnd) % 623
        for k in range(N - 1):
            i = i - 1
            if i <= 0:
                i += 623
            state[i] = ((state[i] + i) ^ ((state[i-1] ^ (state[i-1] >> 30)) * 1566083941)) % uint32_mask
            state[0] = state[N-1]
        origin_state = [0 for _ in range(N)]
        origin_state[0] = 19650218
        for i in range(1, N):
            origin_state[i] = (1812433253 * (origin_state[i-1] ^ (origin_state[i-1] >> 30)) + i) % uint32_mask
        origin = origin_state[:]
        # start to find the key
        key = [0 for i in range(keylen)]
        if lower == None:
            for i in range(keylen - 623):
                key[i] = 1+i
        else:
            if lower.bit_length() > 32 * (keylen - 623):
                self.logger.error("Too much fixed bits")
                return
            for i in range(keylen - 623):
                key[i] = (lower+i) % uint32_mask
                lower >>= 32
        i, j = 1, 0
        for _ in range(step1_rnd - 623):
            origin_state[i] = ((origin_state[i] ^ ((origin_state[i-1] ^ (origin_state[i-1] >> 30)) * 0x19660d)) + key[j]) % uint32_mask
            i += 1
            j += 1
            if i >= 624:
                origin_state[0] = origin_state[623]
                i = 1
        for _ in range(N - 1):
            x = (origin_state[i] ^ ((origin_state[i-1] ^ (origin_state[i-1] >> 30)) * 1664525)) % uint32_mask
            key[j] = (state[i] - x) % uint32_mask
            origin_state[i] = ((origin_state[i] ^ ((origin_state[i-1] ^ (origin_state[i-1] >> 30)) * 1664525)) + key[j]) % uint32_mask
            i += 1
            if i == N:
                origin_state[0] = origin_state[N-1]
                i = 1
            j += 1
        
        if smallseed:
            T = self._findMinPeriod(key[2:-1])
            smallkey = key[T:T+2]+key[2:T] if T>1 else key[2:3]
            x1 = ((origin[1] ^ ((origin[0] ^ (origin[0] >> 30)) * 1664525)) + smallkey[0]) % uint32_mask
            x2 = ((origin[2] ^ ((x1 ^ (x1 >> 30)) * 1664525)) + smallkey[1%T]) % uint32_mask
            x3 = ((x1 ^ ((origin_state[keylen-1] ^ (origin_state[keylen-1] >> 30)) * 1664525)) + smallkey[(keylen-1)%T]) % uint32_mask
            if x2==state[2] and x3==state[1]:
                self.logger.info(f"Find a small seed with key period: {T}.")
                return self._mySeed(smallkey)
            else:
                self.logger.error("No small seed found.")
                return 
        return self._mySeed(key)

def check_normal():
    # normal check
    crack = CrackRandom()
    seed = os.urandom(16)
    target = random.Random(seed)

    M = 25000
    length = 12
    times = M//length
    for i in range(times):
        crack.uploadValues(length,target.getrandbits(length))
    RNG = crack.randomPredict()
    
    assert RNG.getstate() == random.Random(seed).getstate()

def check_seed():
    # check with small seed
    crack = CrackRandom()
    seed = random.SystemRandom().randint(0, 1<<128)
    crack.state = random.Random(seed).getstate()[1][:-1]
    myseed = crack.getSeed(smallseed=True)
    assert seed == myseed

    # check with different keylen and lower
    crack = CrackRandom()
    seed = random.SystemRandom().randint(0, 1<<128)
    crack.state = random.Random(seed).getstate()[1][:-1]
    lower = 0x1145141919810
    myseed = crack.getSeed(keylen=700, lower=lower)
    assert myseed & 0xFFFFFFFFFFFFFFFF == lower
    assert random.Random(seed).getstate() == random.Random(myseed).getstate()

def check_randomlength():
    # check with random bitlength
    crack = CrackRandom()
    seed = os.urandom(16)
    target = random.Random(seed)

    leakbits = 0
    M = 30000 # Need more to make the rank of the matrix = 19937, should fail if M = 19968.
    while leakbits < M:
        length = random.SystemRandom().randint(10,20)
        leakbits += length
        crack.uploadValues(length,target.getrandbits(length))
    RNG = crack.randomPredict()
    
    assert RNG.getstate() == random.Random(seed).getstate()

def check_randomlengthwithunknown():
    # check with random bitlength and unknown bits
    crack = CrackRandom()
    seed = os.urandom(16)
    target = random.Random(seed)

    leakbits = 0
    M = 36000 # Need more to make the rank of the matrix = 19937, should fail if M = 19968.
    while leakbits < M:
        length = random.SystemRandom().randint(10,20)
        known = random.SystemRandom().random() > 0.005
        if known:
            leakbits += length
        else:
            target.getrandbits(length)
        crack.uploadValues(length,target.getrandbits(length) if known else 0, known)
    RNG = crack.randomPredict()
    
    assert RNG.getstate() == random.Random(seed).getstate()

def check_randomlengthwithunknownandseed():
    # check with random bitlength and unknown bits and seed
    crack = CrackRandom()
    seed = os.urandom(16)
    target = random.Random(seed)

    leakbits = 0
    M = 36000 # Need more to make the rank of the matrix = 19937, should fail if M = 19968.
    while leakbits < M:
        length = random.SystemRandom().randint(10,20)
        known = random.SystemRandom().random() > 0.005
        if known:
            leakbits += length
        else:
            target.getrandbits(length)
        crack.uploadValues(length,target.getrandbits(length) if known else 0, known)
    RNG = crack.randomPredict()
    myseed = crack.getSeed(smallseed=True)

    assert int.from_bytes(seed + hashlib.sha512(seed).digest(), "big") == myseed

    
if __name__ == "__main__":
    check_normal()
    # check_seed()
    # check_randomlength()
    # check_randomlengthwithunknown()
    # check_randomlengthwithunknownandseed()