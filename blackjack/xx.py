# -*- coding: utf-8 -*-
import z3
import sys
from math import floor
from collections import deque


class cycle:
    def __init__(self, c):
        self._c = c
        self._index = -1

    def __next__(self):
        self._index += 1
        if self._index >= len(self._c):
            self._index = 0
        return self._c[self._index]

    def previous(self):
        self._index -= 1
        if self._index < 0:
            self._index = len(self._c)-1
        print(self._c[self._index])
        return self._c[self._index]


class Card():
    def __init__(self, v, s):
        self.v = v
        self.s = s

    def __str__(self) -> str:
        if self.v == -1:
            return "(Card not shown)"
        s = ""
        if self.v == 1:
            s += "Ace"
        elif self.v == 11:
            s += "Jack"
        elif self.v == 12:
            s += "Queen"
        elif self.v == 13:
            s += "King"
        else:
            s += str(self.v)
        s += " of "
        if self.s == 1:
            s += "Clubs"
        elif self.s == 2:
            s += "Diamonds"
        elif self.s == 3:
            s += "Hearts"
        elif self.s == 4:
            s += "Spades"

        return s

    def __add__(self, other) -> int:
        v = self.v + other.v
        return v

    def __sub__(self, other) -> int:
        v = self.v - other.v
        return v

    def setValue(self, v):
        self.v = v
        self.s = 999

    def getValue(self):
        return self.v

    # def __add__(self, other: int) -> int:
    #     print(type(other))
    #     print(type(self.v))
    #     v = self.v + other
    #     return v


class Deck():
    def __init__(self) -> None:
        self.deck = []
        self.count = 51
        for i in range(1, 5):
            for j in range(1, 14):
                self.deck.append(Card(j, i))

    def shuffle(self, collection):
        cycledCollection = cycle(collection)
        for i in range(51, -1, -1):
            r = floor((i+1)*next(cycledCollection))
            temp = self.deck[r]
            self.deck[r] = self.deck[i]
            self.deck[i] = temp

    def __str__(self) -> str:
        out = ""
        for i in range(self.count, -1, -1):
            out += str(self.deck[i]) + "\n"
        return out

    def winnerMoves(self):
        vPlayerHand = Card(0, 0)
        vComputerHand = Card(0, 0)
        cdeck = deque(self.deck)

        # the first dealt hands
        cdeck.rotate(1)
        current = cdeck[0]
        vPlayerHand.setValue(vPlayerHand + current)
        cdeck.rotate(1)
        current = cdeck[0]
        vComputerHand.setValue(vComputerHand+current)
        cdeck.rotate(1)
        current = cdeck[0]
        vPlayerHand.setValue(vPlayerHand + current)
        cdeck.rotate(1)
        current = cdeck[0]
        vComputerHand.setValue(vComputerHand + current)

        i = 0
        while(i < 4):
            cdeck.rotate(1)
            current = cdeck[0]
            vPlayerHand.setValue(vPlayerHand + current)
            if (vPlayerHand.getValue() <= 21):
                print("Your move: HIT")
            else:
                vPlayerHand.setValue(vPlayerHand - current)
                print("Your move: STAND")
                current = cdeck[0]
                vComputerHand.setValue(vComputerHand+current)
                print("Dealer hand with these moves: " +
                      str(vComputerHand.getValue()))
                print("Your hand with these moves: " +
                      str(vPlayerHand.getValue()))
                if((vComputerHand.getValue() >= vPlayerHand.getValue()) and vComputerHand.getValue() <= 21):
                    print("Its a loosing game :(")
                else:
                    print("Winning game! :)) ")
                break
            i = i + 1


class XorShift128PlusFirefox(object):
    def __init__(self, s0, s1):
        self.s0 = s0
        self.s1 = s1
        self.state = [s0, s1]

    def current_double(self):
        val = (self.s0 + self.s1) & 0x1fffffffffffff
        return float(val) / 2**53

    def next(self):
        s1 = self.state[0]
        s0 = self.state[1]

        self.state[0] = s0
        s1 ^= (s1 << 23)
        s1 &= 0xffffffffffffffff
        self.state[1] = s1 ^ s0 ^ (s1 >> 17) ^ (s0 >> 26)

        random_val = (self.state[1] + s0) & 0xffffffffffffffff

        return random_val

    def next_double(self):
        return float(self.next() & 0x1fffffffffffff) / 2**53


class Cracker(object):
    def __init__(self, known_values):
        # State variables are two 64-bit numbers.
        self.s0 = z3.BitVec('s0', 64)
        self.s1 = z3.BitVec('s1', 64)
        self.state = [self.s0, self.s1]

        # Solver class is a class to which we can add
        # equations that we will want to solve in the long run
        self.solver = z3.Solver()

        # The known variable will contain known values of
        # pseudo-random numbers generated in Firefox.
        self.known = known_values

    def next(self):
        s1 = self.state[0]
        s0 = self.state[1]

        self.state[0] = s0
        s1 ^= (s1 << 23)
        self.state[1] = s1 ^ s0 ^ z3.LShR(s1, 17) ^ z3.LShR(s0, 26)

        return self.state[1] + s0

    def crack(self):
        # Because of the way numbers are generated in Firefox,
        # from the number calculated by 3 we take only the youngest 53
        # Bits. In turn the floating-point number should be replaced by the following
        # integers by multiplying it by 2**53.
        for val in self.known:
            self.solver.add((self.next() & 0x1fffffffffffff)
                            == int(val * 2**53))
        if self.solver.check() != z3.sat:
            raise Exception("Not solved!")

        model = self.solver.model()
        s0 = model[self.s0].as_long()
        s1 = model[self.s1].as_long()

        return (s0, s1)


def main():
    # Take one argument from the command line representing
    # several floating-point numbers separated by commas.
    known_values = [float(v) for v in sys.argv[1].split(",")]

    # We „break” the state of the random number generator.
    cracker = Cracker(known_values)
    (s0, s1) = cracker.crack()

    # We use the calculated generator state to calculate
    # the next pseudo-random numbers.
    prng = XorShift128PlusFirefox(s0, s1)

    # we generate a collection of 52 next random values to predict the state of the shuffled deck.
    collection = []
    for _ in range(54):
        collection.append(prng.next_double())

    # remove already generated values
    collection = collection[3:]

    deck = Deck()
    deck.shuffle(collection)
    print("[+] predicted state of the shuffled deck:")
    print(deck)
    print("[+] Riscufefe for the win..")
    deck.winnerMoves()


if __name__ == '__main__':
    main()
