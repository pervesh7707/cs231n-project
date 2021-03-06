import cocotb

from cocotb.result      import TestFailure
from cocotb.clock       import Clock
from cocotb.triggers    import RisingEdge, FallingEdge, ClockCycles, ReadOnly
from cocotb.result      import TestFailure

class MultipyAccumulateCellTB(object):
    def __init__(self, dut):
        self.dut    = dut
        self.weight = None

    @cocotb.coroutine
    def set_weight(self, weight):
        self.dut._log.debug("Setting weight to %d" % (weight,))
        self.dut.weight_in  = weight
        self.dut.weight_set = 1
        self.weight         = weight
        yield RisingEdge(self.dut.clock)
        self.dut.weight_in  = 0
        self.dut.weight_set = 0

    @cocotb.coroutine
    def multiply(self, data, accumulator=0):
        # Check that we've set a weight
        if self.weight == None:
            raise TestFailure(
                "No weight set in tb yet!")

        # Perform the MAC operation
        self.dut.data_in        = data
        self.dut.accumulator_in = accumulator
        self.dut.mac_stall_in   = 0
        yield RisingEdge(self.dut.clock)

        # Get the result and compare
        yield ReadOnly()
        acc_out  = self.dut.accumulator_out
        data_out = self.dut.data_out

        acc_cor = data * self.weight + accumulator
        if acc_out != acc_cor:
            raise TestFailure(
                "Result was %d instead of %d" % (acc_out, acc_cor))

        if data_out != data:
            raise TestFailure(
                "Data out was %d instead of %d" % (data_out, data))

    @cocotb.coroutine
    def reset(self, cycles=1):
        self.dut._log.debug("Resetting DUT")
        self.dut.weight_in      = 0
        self.dut.weight_set     = 0
        self.dut.data_in        = 0
        self.dut.accumulator_in = 0
        self.dut.mac_stall_in   = 0
        self.dut.reset          = 1
        yield ClockCycles(self.dut.clock, cycles)
        self.dut.reset = 0
        self.dut._log.debug("Out of reset")

    @cocotb.coroutine
    def wait(self, cycles=1):
        yield ClockCycles(self.dut.clock, cycles)

@cocotb.test()
def mac_test(dut):
    log = cocotb.logging.getLogger("cocotb.test")

    # Start clock on seperate execution thread
    cocotb.fork(Clock(dut.clock, 100).start())

    # Create the testbench
    tb = MultipyAccumulateCellTB(dut)

    # Toggle reset before the actual test
    yield tb.reset(2)

    # Set the inputs and outputs
    yield tb.set_weight(10)
    yield tb.multiply(5)
    yield tb.wait(3)
