import gdb
import re

internal_list = []  # in use heap addresses as gdb.Value with type long*
breakpoints = [] #ireelevant for now, but saving our breakpoints might be useful at some point
memalign_address = 0 #important to save the memalign pointer since the function is handles by more than one breakpoint
symbol_strings = [] # list of all symbol strings added using heapvis-symbol

def set_BPs():
    global breakpoints
    # check for libc is loaded
    objs = gdb.objfiles()
    libc_loaded = False
    for obj in objs:
        if "libc" in obj.filename:
            libc_loaded = True
            break
    if not libc_loaded:
        return 
    malloc_lengths = [0xad,0x13a,0x158,0x3bc,0x41b]
    calloc_lengths= [0x206,0xa5]
    memalign_lengths=[(0x87795 - 0x87750),(0x877a6 - 0x87750)]
    realloc_length = 0x866d3 - 0x865c0 

    #init breakpoints at the return statements of malloc
    for l in malloc_lengths:
      breakpoints.append(alloc_BP("*(__libc_malloc)+"+str(hex(l)),internal=True)) 

    #init breakpoints at the return address of calloc
    for l in calloc_lengths:
      breakpoints.append(alloc_BP("*(__libc_calloc)+"+str(hex(l)),internal=True)) 

    #init breakpoints at the return address of posix_memallign (slightly more complicated)
    for l in memalign_lengths:
      breakpoints.append(memalign_end_BP("*(posix_memalign)+"+str(hex(l)),internal=True))

    #init breakpoints at the return address of realloc 
    breakpoints.append(alloc_BP("*(__libc_realloc)+"+str(hex(realloc_length)),internal=True)) 

    #init free breakpoint at the start of realloc, posix_memalign and free

    breakpoints.append(free_BP("__libc_free",internal=True))
    breakpoints.append(memalign_start_BP("posix_memalign",internal=True)) 
    breakpoints.append(free_BP("realloc",internal=True)) 

def on_new_objfile(new_objfile_event):
    global breakpoints
    if "libc" in new_objfile_event.new_objfile.filename:
        for bp in breakpoints:
            bp.delete()
        breakpoints = []
        set_BPs()


class alloc_BP (gdb.Breakpoint):
      def stop (self):
        address = gdb.parse_and_eval("$rax").cast(gdb.lookup_type("long").pointer()) #get the address back and add it to the internal list
        if address not in internal_list:
          internal_list.append(address)
        return False

class memalign_start_BP (gdb.Breakpoint):
      def stop (self):
        global memalign_address
        memalign_address = gdb.parse_and_eval("$rdi").cast(gdb.lookup_type("long").pointer()) #get the address back and add it to the internal list
        return False
      
class memalign_end_BP (gdb.Breakpoint):
      def stop (self):
        global memalign_address
        address = gdb.parse_and_eval("*"+memalign_address)
        if address != 0 and address not in internal_list:
          internal_list.append(address)
        return False
      

class free_BP (gdb.Breakpoint):
      def stop (self):
        address = gdb.parse_and_eval("$rdi").cast(gdb.lookup_type("long").pointer()) #get the address back and add it to the internal list
        if address in internal_list:
          internal_list.remove(address)
        return False

class HeapvisCmd(gdb.Command):
    """visualizes the heap"""

    def __init__(self):
        super().__init__(
            "heapvis", gdb.COMMAND_USER
        )

    def complete(self, text, word):
        # the optional parameters are symbols, so use that for the first 2 autocompletion
        if len(text.split(" ")) <= 2:
            return gdb.COMPLETE_SYMBOL
        else:
            return gdb.COMPLETE_NONE

    def invoke(self, args_str, from_tty):
        global internal_list
        args = gdb.string_to_argv(args_str)
        heap_range = self.get_heap_range()
        if heap_range == None:
            print("I found no heap")
            return
        # use the given bound if given, else use heap_range as bounds
        if len(args) == 0:
            bounds = heap_range
        elif len(args) == 1:
            bounds = (gdb.parse_and_eval(args[0]), heap_range[1])
        elif len(args) == 2:
            bounds = [gdb.parse_and_eval(x) for x in args]
        else:
            print("heapvis expects 0, 1 or 2 arguments but more were given\n"+\
                    "heapvis [lowerBound [, upperBound]]")
        main_arena = self.get_main_arena()
        if main_arena == None:
            print("Unable to locate the main arena")
            return
        tcache = self.get_tcache()
        if tcache == None:
            print("Unable to locate the tcache")
            return
        # create a list of tupels (chunk_start_index, where)
        #   with where 0: in_use, 1: in the tchache, 2: in the arena
        # start with the in use chunks
        all_chunks = [[x, 0, ""] for x in internal_list]
        # traverse all tchache chunks
        for i in range(0x10, 0x50):
            all_chunks += [[x, 1, ""] for x in self.traverse(tcache+i*0x8, 0)]
        # and all singly linked bins from the main arena
        for i in range(0x0, 0xb):
            if 0x10+i*0x8 == 0x60:
                continue
            all_chunks += [[x, 2, ""] for x in self.traverse(main_arena+0x10+i*0x8, 2)]
        # the topchunk has the info TOPCHUNK
        all_chunks += [[(main_arena+0x60).cast(gdb.lookup_type("long").pointer().pointer()).dereference()+2, 2, "TOP CHUNK"]]
        # and all other chunks from the main arena
        for i in range(0x6, 0x84):
            all_chunks += [[x, 2, ""] for x in self.traverse(main_arena+0x10+i*0x10, 2)]
        # sort all chunks in the all_chunks list by address
        all_chunks.sort(key=lambda x: x[0])
        # use only the ones, that are on the heap
        all_chunks = [x for x in all_chunks if bounds[0] <= x[0] <= bounds[1]]
        # add symbol names
        self.look_up_symbols()
        all_chunks = [self.add_symbol_name(x) for x in all_chunks]
        # make sure no list has overlapping chunks
        all_lists = self.split_all_chunks(all_chunks)
        self.print_chunks(all_lists)


    def get_heap_range(self):
        ub = 0x00
        lb = 0xffffffffffffffff
        try:
            mappings = gdb.execute("info proc mappings",to_string=True)
        except:
            #print("error ocurred while trying to get the mappings, are you sure there is a process running?")
            return None
        mappings_lines = mappings.split("\n")
        # look for a line containing " [heap]\n" to find the upper and lower
        # bound of the heap breaks if the program is called [heap] and 
        # run from the same directory
        for line in mappings_lines:
            if line[-7:] == " [heap]":
                split_line = line.split(" ")
                # find the first number in that line
                i = 0
                while split_line[i] == "":
                    i += 1
                if lb > int(split_line[i], 16):
                    lb = int(split_line[i], 16)
                i += 1
                while split_line[i] == "":
                    i += 1
                if ub < int(split_line[i], 16):
                    ub = int(split_line[i], 16)
        return (lb,ub) if ub >= lb else None

    def get_main_arena(self):
        # use debug symbols if possible

        # if there are no debug symbols for libs 
        # guess the main arena address based of the __malloc_hook
        malloc_hook = gdb.parse_and_eval("(void*) &__malloc_hook")
        return malloc_hook + 0x10

    def get_tcache(self):
        # that's how malloc gets the tcache
        # we assume only ont thread, and only one tcache
        tcache = gdb.parse_and_eval("(void**) ($fs_base-0x50)").dereference()
        return tcache

    def traverse(self, startval, of):
        res = []
        if not isinstance(startval, gdb.Value):
            startval = gdb.Value(startval.to_bytes(8, "little"), gdb.lookup_type("long"))
        # make sure startval is of type pointer, so that we can dereference it
        startval = startval.cast(startval.type.pointer())
        # after dereferencing make sure the value points to the next pointer (+of)
        val = startval.dereference()
        val = val.cast(val.type.pointer()) + of
        while val > of*0x8 and val != startval:
            nval = val.cast(gdb.lookup_type("long").pointer())
            if nval in res:
                print("There is a loop in the next pointers at address 0x%x"%nval)
                break
            res.append(nval)
            val = val.dereference()
            val = val.cast(val.type.pointer())+of
        return res
    
    def look_up_symbols(self):
        global symbol_strings
        self.symbols = []
        for symb in symbol_strings:
            try:
                addr = gdb.parse_and_eval(symb)
                self.symbols.append((symb, addr))
            except:
                """"""

    def add_symbol_name(self, chunk):
        for symb, addr in self.symbols:
            if chunk[0] == addr:
                # add the symbol name to the chunk
                if chunk[2] == "":
                    chunk[2] = symb
                else:
                    chunk[2] += "\n" + symb
        return chunk

    def split_all_chunks(self, chunks):
        """return a list of lists of chunks. Within each list the chunks are sorted by start address and don't overlap"""
        res = [[]]
        end_of_list = [0]
        for chunk in chunks:
            addr = chunk[0]-2
            size = (chunk[0]-1).dereference() & ~0x7
            end = addr + size/8
            added = False
            for i in range(len(end_of_list)):
                if end_of_list[i] <= addr:
                    res[i].append(chunk)
                    end_of_list[i] = end
                    added = True
                    break
            if not added:
                res.append([chunk])
                end_of_list.append(end)
        return res
    
    class Chunk_list_print_helper:
        empty_line = " "*20 + "#"
        sep_line = "#"*21
        def __init__(self, list):
            self.list = list
            self.cur = 0
            self.printing = False
            self.load_values()
        
        def done(self):
            return self.cur >= len(self.list)

        def next_num(self):
            if self.done():
                return 0xffffffffffffffff
            if self.printing:
                return self.end
            else:
                return self.addr
        
        def veto(self, num):
            return self.printing and num >= self.end and self.next_line < len(self.lines)

        def load_values(self):
            if self.done():
                return
            c_addr = self.list[self.cur][0]
            self.addr = c_addr-2
            self.size = (c_addr-1).dereference() & ~0x7
            self.end = self.addr + self.size/8
            A = (c_addr-1).dereference() & 0x4
            M = (c_addr-1).dereference() & 0x2
            P = (c_addr-1).dereference() & 0x1
            fd = c_addr.dereference()
            bw = (c_addr+1).dereference()
            place = "in use" if self.list[self.cur][1] == 0 else \
                    "in tchache" if self.list[self.cur][1] == 1 else \
                    "in the arena"
            
            self.lines = []
            self.lines.append(" flags: {:1d} {:1d} {:1d}       #".format(int(A), int(M), int(P)))
            self.lines.append(" {:<18} #".format(place))
            self.lines.append(" size: {:<12} #".format(str(self.size)))
            if self.list[self.cur][1] != 0:
                self.lines.append(" fd: {:<14} #".format(str(fd)))
            if self.list[self.cur][1] == 2:
                self.lines.append(" bw: {:<14} #".format(str(bw)))
            if self.list[self.cur][2] != "":
                self.lines += [" {:<18} #".format(x) for x in self.list[self.cur][2].split("\n")]
            self.next_line = 0

        def get_line(self, veto, num):
            if self.done():
                return self.empty_line
            if self.printing and self.next_line < len(self.lines):
                res = self.lines[self.next_line]
                self.next_line += 1
                return res
            
            if veto or self.next_num() != num:
                return self.empty_line

            if self.printing:
                # end this chunk if needed start next
                old_end = self.end
                self.cur += 1
                self.load_values()
                if self.addr == old_end:
                    self.printing = True
                else:
                    self.printing = False
                return self.sep_line
            else:
                self.printing = True
                return self.sep_line

    def print_chunks(self, lists):
        res = ""
        helpers = [self.Chunk_list_print_helper(x) for x in lists]
        while not all([x.done() for x in helpers]):
            # get the next line number that has to be printed at the left
            num = min([x.next_num() for x in helpers])
            # am I allowed to print that number now?
            veto = any([x.veto(num) for x in helpers])
            if veto:
                res += " "*0x10 + "#"
            else:
                res += "{:>15} #".format(str(num))
            
            for helper in helpers:
                res += helper.get_line(veto, num)
            res += "\n"
        print(res)

class HeapvisSymbolCmd(gdb.Command):
    """Add a symbol to a chunk in the visualisation"""

    def __init__(self):
        super().__init__(
            "heapvis-symbol", gdb.COMMAND_USER
        )

    def complete(self, text, word):
        # all parameters are symbols
        return gdb.COMPLETE_SYMBOL

    def invoke(self, args_str, from_tty): 
        global symbol_strings
        args = gdb.string_to_argv(args_str)
        for symb in args:
            try:
                addr = gdb.parse_and_eval(symb)
            except:
                print("failed to parse the symbol %s. Ignoring that symbol"%symb)
            if not symb in symbol_strings:
                symbol_strings.append(symb)
                print("added symbol %s"%symb)
            else:
                print("%s is already known"%symb)

# try to set the breakpoints now
set_BPs()
# renew the breakpoints every time a new objfile with libc in its name is loaded
gdb.events.new_objfile.connect(on_new_objfile)
# add the heapvis command
HeapvisCmd()
# and the heapvis-symbol command
HeapvisSymbolCmd()
