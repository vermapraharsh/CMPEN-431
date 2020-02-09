#Praharsh Verma
#CMPEN431 Project 2

import logging
from dataStructures import *
class scheduler:
    def __init__ (self, infilename, outfilename):
        ARCH_REGS_COUNT = 32
        self.input = self.parse_input_file(infilename)
        (self.num_phy_regs, self.issue_width) = next(self.input)
        self.out_file = open(outfilename, "w")
        self.decode_queue = pipeline_stage(self.issue_width)
        self.rename_queue = pipeline_stage(self.issue_width)
        self.dispatch_queue = pipeline_stage(self.issue_width)
        self.issue_queue = []
        self.reorder_buffer = []
        self.lsq = load_store_queue()
        self.executing_queue = []
        self.map_table = reg_map(ARCH_REGS_COUNT)
        self.free_list = free_list(self.num_phy_regs)
        self.ready_table = ready_queue(self.num_phy_regs)
        self.freeing_registers = []
        for register in range(ARCH_REGS_COUNT):
            self.map_table.put(register, self.free_list.get_free_reg())
        self.instructions = []
        self.cycle = 0
        self.fetching = True
        self.has_progressed = True

    def schedule (self):
        self.fetching = True
        self.has_progressed = True
        while self.is_scheduling() and self.has_progressed:
            logging.info("Scheduling: %s" % self)
            self.has_progressed = False
            self.commit()
            self.writeback()
            self.issue()
            self.dispatch()
            self.rename()
            self.decode()
            self.fetch()
            self.advance_cycle()

    def advance_cycle (self):
        for free_reg in self.freeing_registers:
            self.free_list.free(free_reg)
        self.freeing_registers = []
        self.cycle += 1
        logging.debug("Advanced scheduler to cycle # %d" % self.cycle)

    def made_progress (self):
        self.has_progressed = True

    def is_scheduling (self):
        return (
            self.fetching
            or any(not inst.has_commited() for inst in self.instructions))

    def fetch_inst (self):
        try:
            return next(self.input)
        except StopIteration:
            self.fetching = False
            return None

    def fetch (self):
        fetched = 0
        while self.fetching and fetched < self.issue_width:
            inst = self.fetch_inst()
            if inst is not None:
                inst.fetch_cycle = self.cycle
                self.instructions.append(inst)
                self.decode_queue.pushQ(inst)
                fetched += 1
                self.made_progress()
                logging.debug("Fetched: %s" % inst)

    def decode (self):
        while not self.decode_queue.is_empty():
            inst = self.decode_queue.popQ()
            inst.decode_cycle = self.cycle
            self.rename_queue.pushQ(inst)
            self.made_progress()
            logging.debug("Decoded: %s" % inst)

    def rename (self):
        while not self.rename_queue.is_empty():
            inst = self.rename_queue.popQ()
            if inst.inst != "S":
                if self.free_list.is_free():
                    if inst.src_reg_0:
                        inst.src_reg_0 = self.map_table.get(inst.src_reg_0)
                    if inst.src_reg_1:
                        inst.src_reg_1 = self.map_table.get(inst.src_reg_1)
                    self.map_table.put(inst.dst_reg,self.free_list.get_free_reg())
                    inst.overwritten = inst.dst_reg
                    inst.dst_reg = self.map_table.get(inst.dst_reg)
                    inst.renamed = True
                else:
                    self.rename_queue.insertQ(inst)
                    break
            elif inst.inst == "S":
                inst.src_reg_0 = self.map_table.get(inst.src_reg_0)
                inst.src_reg_1 = self.map_table.get(inst.src_reg_1)
                inst.renamed = True
            if inst.renamed == True:
                if inst.dst_reg:
                    self.ready_table.clear(inst.dst_reg)
                inst.rename_cycle = self.cycle
                self.dispatch_queue.pushQ(inst)
                self.made_progress()
                logging.debug("Renamed: %s" % inst)

    def dispatch (self):
        while not self.dispatch_queue.is_empty():
            inst = self.dispatch_queue.popQ()
            self.issue_queue.append(inst);
            self.reorder_buffer.append(inst)
            if (inst.inst == "L" or inst.inst == "S"):
                self.lsq.append(inst)
            inst.dispatch_cycle = self.cycle
            self.made_progress()
            logging.debug("Dispatched: %s" % inst)

    def issue (self):
        issued = 0
        for inst in list(self.issue_queue):
           if(self.is_inst_ready(inst) and issued < self.issue_width ):
                issued = issued + 1
                self.issue_queue.remove(inst)
                inst.issue_cycle = self.cycle
                self.executing_queue.append(inst)
                self.made_progress()
                logging.debug("Issued: %s" % inst)

    def writeback (self):
        for inst in list(self.executing_queue):
            if inst.inst == "L":
                if self.lsq.can_execute(inst):
                    self.ready_table.ready(inst.dst_reg)
                    self.lsq.remove(inst)
                    inst.writeback_cycle = self.cycle
                    self.executing_queue.remove(inst)
                    self.made_progress()
                    logging.debug("Writeback Load/Store: %s" % inst)
            elif inst.inst == "S":
                self.lsq.remove(inst)
                inst.writeback_cycle = self.cycle
                self.executing_queue.remove(inst)
                self.made_progress()
                logging.debug("Writeback Load/Store: %s" % inst)
            else:
                self.ready_table.ready(inst.dst_reg)
                inst.writeback_cycle = self.cycle
                self.executing_queue.remove(inst)
                self.made_progress()
                logging.debug("Writeback: %s" % inst)

    def commit (self):
        for inst in list(self.reorder_buffer):
            if inst.has_writtenback():
                if (inst.inst != "S"):
                    self.freeing_registers.append(inst.dst_reg)
                self.reorder_buffer.remove(inst)
                inst.commit_cycle = self.cycle
                self.made_progress()
                logging.debug("Committed: %s" % inst)
            else:
                break

    def is_inst_ready (self, inst):

        if (not self.ready_table.is_ready(inst.src_reg_0)):
            return False

        if (inst.src_reg_1 is not None) and (not self.ready_table.is_ready(inst.src_reg_1)):
            return False

        if inst.is_load_store_inst():
            return self.lsq.can_execute(inst)

        return True

    def parse_input_file (self, infilename):
        PHY_REG_COUNT_MIN = 32
        try:
            with open(infilename, 'r') as file:
                config_parser = re.compile("^(\\d+),(\\d+)$")
                inst_parser = re.compile("^([RILS]),(\\d+),(\\d+),(\\d+)$")
                header = file.readline()
                configs = config_parser.match(header)
                if configs:
                    (num_phy_reg, issue_width) = configs.group(1, 2)
                    num_phy_reg = int(num_phy_reg)
                    issue_width = int(issue_width)
                    if num_phy_reg < PHY_REG_COUNT_MIN:
                        print("Error: Invalid input file header: Number of "
                                "physical register is less than allowed minimum of %d" % (PHY_REG_COUNT_MIN))
                        sys.exit(1)
                    yield (num_phy_reg, issue_width)
                else:
                    print("Error: Invalid input file header!")
                    sys.exit(1)
                for (index, line) in enumerate(file):
                    configs = inst_parser.match(line)
                    if configs:
                        (Insts, op0, op1, op2) = configs.group(1, 2, 3, 4)
                        yield instruction(index, Insts, int(op0), int(op1), int(op2))
                    else:
                        print("Error: Invalid inst_set: %s" % (line))
                        sys.exit(1)
        except IOError:
            print("Error parsing input file!")
            sys.exit(1)

    def generate_output_file (self):
        if self.is_scheduling():
            self.out_file.write("")
            self.out_file.close()
            return
        for inst in self.instructions:
            self.out_file.write("%s,%s,%s,%s,%s,%s,%s\n" % (
                inst.fetch_cycle,
                inst.decode_cycle,
                inst.rename_cycle,
                inst.dispatch_cycle,
                inst.issue_cycle,
                inst.writeback_cycle,
                inst.commit_cycle,))
        self.out_file.close()

    def __str__ (self):
        return "[out_of_order_scheduler cycle=%d]" % (self.cycle)
