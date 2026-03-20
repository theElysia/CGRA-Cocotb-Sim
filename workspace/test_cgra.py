"""
Copyright (c) 2025 CGRA
All rights reserved.

This module contains a cocotb testbench for running a CGRA kernel with pytest

"""

###########
## Import from cocotb
###########
import os
import logging
import numpy as np

import cocotb

# from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.regression import TestFactory
from cocotb.utils import get_sim_time

# from cocotbext.axi import AxiBus, AxiMaster, AxiLiteBus, AxiLiteMaster, AxiRam

## set path for  cgra_test_pylib
from test_runif import (
    DeviceInfo,
    DeviceData,
    DeviceConfig,
    DeviceStream,
    DeviceRuntime,
    Axi4LiteTb,
)
import test_runif

## ================================
## Import from kernel function py
## ================================
# @zwzhong
from IntVecAdd import IntVecAdd


tests_dir = os.path.dirname(__file__)


# ==============================
# Main cocotb coroutine
# ==============================
def random_init_i16(shape, low=0, high=30):
    return np.random.randint(low, high + 1, size=shape, dtype=np.int16)


def zero_init_i16(shape):
    return np.zeros(shape, dtype=np.int16)


# ==============================
# Main cocotb coroutine
# ==============================
async def cgra_run_top_intvecadd(dut) -> None:
    """
    Run a CGRA kernel test.

    Args:
        dut: cocotb DUT object (Design Under Test).
    """
    # Reset DUT
    axibus = Axi4LiteTb(dut)
    await axibus.cycle_reset()
    axibus.log.info("[CGRA] Starting CGRA kernel test (intvecadd)")

    # set log level
    # axibus.log.setLevel(logging.WARNING)
    # logging.getLogger("cocotb.test_cgra.axi").disabled = True
    # logging.getLogger("cocotb.test_cgra.axil").disabled = True
    # logging.getLogger("test_runif").setLevel(logging.DEBUG)

    # Prepare test data
    a = random_init_i16((20))
    b = random_init_i16((20))
    c = zero_init_i16((20))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    reg_json_path = os.path.join(base_dir, "../circuits/axilite_spec.json")
    adg_json_path = os.path.join(base_dir, "../circuits/vitra_cgra_adg.json")
    device1 = test_runif.create_device_info_factory(
        reg_json_path=reg_json_path, adg_json_path=adg_json_path
    )

    runtime = DeviceRuntime(
        dut=dut,
        axi=axibus.axi,
        axil=axibus.axil,
        axi_size=axibus.axi.write_if.max_burst_size,
    )

    runtime.add_device(device1)

    # Start kernel execution
    start_time = get_sim_time(units="ns")
    await IntVecAdd(runtime, a, b, c)

    await runtime.synchronize_all()
    await RisingEdge(dut.clk)

    print("vec a", a[:20])
    print("vec b", b[:20])
    print("vec c", c[:20])

    end_time = get_sim_time(units="ns")
    axibus.log.info(f"Sim time: {end_time - start_time} ns")


# ==============================
# TestFactory registration
# ==============================
if cocotb.SIM_NAME:
    cgra_run_top = cgra_run_top_intvecadd
    factory = TestFactory(cgra_run_top)
    factory.generate_tests()

# if __name__ == "__main__":
#     cgra_run_top
