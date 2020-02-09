import sys
import re
import logging
class instruction:
    def __init__ (self, instr_number, inst, op0, op1, op2):
        self.instr_number = instr_number
        self.inst = inst
        if inst == "I":
            self.src_reg_0 = op1
            self.src_reg_1 = None
            self.immediate = op2
            self.dst_reg = op0
            self.m_access = False
        elif inst == "R":
            self.src_reg_0 = op1
            self.src_reg_1 = op2
            self.immediate = None
            self.dst_reg = op0
            self.m_access = False
        elif inst == "L":
            self.src_reg_0 = op2
            self.src_reg_1 = None
            self.immediate = op2
            self.dst_reg = op0
            self.m_access = True
        elif inst == "S":
            self.src_reg_0 = op0
            self.src_reg_1 = op2
            self.immediate = op1
            self.dst_reg = None
            self.m_access = True
        self.overwritten = None
        self.renamed = False
        self.fetch_cycle = None
        self.decode_cycle = None
        self.rename_cycle = None
        self.dispatch_cycle = None
        self.issue_cycle = None
        self.writeback_cycle = None
        self.commit_cycle = None

    def is_load_inst (self):
        return self.inst == "L"

    def is_store_inst (self):
        return self.inst == "S"

    def is_load_store_inst (self):
        return self.is_load_inst() or self.is_store_inst()

    def has_issued (self):
        return self.issue_cycle is not None

    def has_writtenback (self):
        return self.writeback_cycle is not None

    def has_commited (self):
        return self.commit_cycle is not None

    def __str__ (self):
        return "[inst %d: %s [%s%s]%s -> %s]" % (
            self.instr_number,
            self.inst,
            self.src_reg_0,
            "" if self.src_reg_1 is None else (" " + str(self.src_reg_1)),
            " #%d" % (self.immediate) if self.immediate is not None else "",
            self.dst_reg)

class pipeline_stage:
    def __init__ (self, width):
        self.queue = []

    def pushQ (self, item):
        self.queue.append(item)

    def insertQ (self, item):
        self.queue.insert(0, item)

    def is_empty (self):
        return len(self.queue) == 0

    def popQ (self):
        if self.is_empty():
            raise TypeError("Pull from empty pipeline stage")

        return self.queue.pop(0)

    def __str__ (self):
        return "[pipeline_stage %s]" % (self.queue)

class reg_map:
    def __init__ (self, num_arch_regs):
        self.num_arch_regs = num_arch_regs
        self.mapping_table = [None] * self.num_arch_regs

    def put (self, arch_reg_num, phy_reg_num):
        self.mapping_table[arch_reg_num] = phy_reg_num

    def get (self, arch_reg_num):
        return self.mapping_table[arch_reg_num]

    def __str__ (self):
        return "[reg_map %s]" % (self.mapping_table)

class free_list:

    def __init__ (self, num_phy_regs):
        self.free_list_map = list(range(num_phy_regs))

    def is_free (self):
        return len(self.free_list_map)

    def get_free_reg (self):
        if not self.is_free():
            return TypeError("No free registers")

        return self.free_list_map.pop(0)

    def free (self, reg_num):
        self.free_list_map.append(reg_num)

    def __str__ (self):
        return "[free_list_map %s]" % (self.free_list_map)

class ready_queue:
    def __init__ (self, num_phy_regs):
        self.table = [True] * num_phy_regs

    def is_ready (self, reg_num):
        return self.table[reg_num]

    def ready (self, reg_num):
        self.table[reg_num] = True

    def clear (self, reg_num):
        self.table[reg_num] = False

    def __str__ (self):
        return "[ready_queue %s]" % (
            "".join(map(lambda x: "1" if x else "0", self.table)))

class load_store_queue:
    def __init__  (self):
        self.entries = []

    def append (self, inst):
        self.entries.append(inst)

    def remove (self, inst):
        self.entries.remove(inst)

    def can_execute (self, inst):
        for (index, current_instr) in enumerate(self.entries):
            if current_instr.is_load_inst() or (current_instr.is_store_inst() and index == 0):
                if current_instr == inst:
                    return True
            if current_instr.is_store_inst():
                break
        return False

    def get_executable (self):
        insts = []
        for (index, inst) in enumerate(self.entries):
            if inst.is_load_inst() or (inst.is_store_inst() and index == 0):
                insts.append(inst)
            if inst.is_store_inst():
                break
        return insts
