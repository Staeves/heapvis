# Heapvis

Heapvis is a tool to visualize how the chunks are laid out on the heap. It works by adding the commands `heapvis` and `heapvis-symbol` to gdb.

## Requirements
* gdb with python enabled (to check, run `gdb --config` if the output contains a line like `--with-python=/usr` you are good).
* check the current [limitations](#Limitations).

## Installation
None ;)
But we recommend adding the line `source /path/to/heapvis.py` to your .gdbinit, so that you don't have to call it every time.

## Usage
1. Either add the line `source /path/to/heapvis.py` to your .gdbinit file or execute `source /path/to/heapvis.py` when you start debugging. It is important that heapvis.py is sourced before the program is run, as when sourcing, heapvis sets up a few breakpoints to keep track of all in-use chunks. That means all chunks allocated before sourcing heapvis will not be included in the visualization.
1. debug the program and use `heapvis` and `heapvis-symbol` whenever you want.

```
heapvis [lowerBound [upperBound]]
```
The `heapvis` command generates a visualization of the heap and supports up to two optional arguments. Both can be a symbol or an address.
* When no arguments are given, the entire heap is included in the visualization.
* When one argument is given, it serves as a lower bound, and the visualization includes all chunks on the heap with an address greater than or equal to the given parameter. The chunks address used for the comparison is the address returned by malloc or passed to free.
* When two arguments are given, the first one serves as a lower bound and the second one as an upper bound. The visualization will only include chunks if `lowerBound <= chunkAddress <= upperBound`. The address returned from malloc or passed to free is used as the chunks address.

```
heapvis-symbol symbol [...]
```
The `heapvis-symbol` command takes an arbitrary number of arguments that have to be symbols. All symbols will be stored and included in the output of future `heapvis` calls. For a symbol to be mapped to a chunk in the visualization, it has to resolve to the address returned by malloc or passed to free. A chunk can have none, one, or multiple symbols assigned to it, and a symbol can be assigned to none, one, or multiple chunks (e.g., if two chunks have the same start address). Symbols passed to heapvis-symbol have to map to a value. If a symbol can not be mapped to a chunk or the symbol can no longer be converted to an address when calling `heapvis` the symbol is ignored.

## Limitations
* only supports libc version 2.31 
* not tested with multithreading
* the only supported arena is the main arena

## Examples
The exact c code to generate these examples can be found in the [test](test) folder.
### Example 1
When breaking after this [code](test/example1.c):
```c
void* a = malloc(0x20);
void* b = malloc(0x20);
free(a);
```
Calling `heapvis-symbol a b` followed by `heapvis` results in this output:
```
 0x5649d5b7e290 ######################
                # flags: 0 0 1       #
                # in tchache         #
                # size: 0x30         #
                # fd: 0x0            #
                # a                  #
 0x5649d5b7e2c0 ######################
                # flags: 0 0 1       #
                # in use             #
                # size: 0x30         #
                # b                  #
 0x5649d5b7e2f0 ######################
                # flags: 0 0 1       #
                # in the arena       #
                # size: 0x20d10      #
                # fd: 0x0            #
                # bw: 0x0            #
                # TOP CHUNK          #
 0x5649d5b9f000 ######################

```
### Example 2
[This example](test/example2.c) is intended to show the way overlapping chunks are handeld.
```c
void* a = malloc(0x20);
void* b = a+0x10;
*((long*)(b-0x8)) = 0x21;
free(b);
```
Calling `heapvis-symbol a b` followed by `heapvis` now results in this output:
```
 0x5589de279290 ######################                    #
 0x5589de2792a0 # flags: 0 0 1       ######################
                # in use             # flags: 0 0 1       #
                # size: 0x30         # in tchache         #
                # a                  # size: 0x20         #
                #                    # fd: 0x0            #
                #                    # b                  #
 0x5589de2792c0 ###########################################
                # flags: 0 0 1       #                    #
                # in the arena       #                    #
                # size: 0x20d40      #                    #
                # fd: 0x0            #                    #
                # bw: 0x0            #                    #
                # TOP CHUNK          #                    #
 0x5589de29a000 ######################                    #

```

### Example 3
In [this example](test/example3.c), three chunks are placed in the tcache, and then the next pointer of c gets manipulated to point to a, resulting in b to disappear from the tcache. Because future malloc calls will not return b, the chunk is no longer included in the visualization.
```c
void* a = malloc(0x20);
void* b = malloc(0x20);
void* c = malloc(0x20);
free(a);
free(b);
free(c);
*((long*)(c)) = a;      // corrupt the fd pointer of c
```
Calling `heapvis-symbol a b c` followed by `heapvis` results in:
```
 0x55f0180e7290 ######################
                # flags: 0 0 1       #
                # in tchache         #
                # size: 0x30         #
                # fd: 0x0            #
                # a                  #
 0x55f0180e72c0 ######################
 0x55f0180e72f0 ######################
                # flags: 0 0 1       #
                # in tchache         #
                # size: 0x30         #
                # fd: 0x55f0180e72a0 #
                # c                  #
 0x55f0180e7320 ######################
                # flags: 0 0 1       #
                # in the arena       #
                # size: 0x20ce0      #
                # fd: 0x0            #
                # bw: 0x0            #
                # TOP CHUNK          #
 0x55f018108000 ######################

```
## The inner workings
When calling `source heapvis.py` the script adds the `heapvis` command to gdb and inserts multiple breakpoints. None of the breakpoints will require user interaction to continue. The breakpoints can be divided into two types: the first type of breakpoints will break at the `ret` instructions of all functions that allocate memory, such as `malloc` or `calloc`. They will be used to add all allocated chunks to an internal list of in-use addresses. The other type of breakpoint will be at the beginning of all functions that can free chunks, such as `free`. They are used to remove addresses from the internal list of in-use addresses. In addition to that, the script registers an event for every time a new objfile is loaded to add the breakpoints in cases where the libc was not yet loaded while sourcing heapvis.py.
When the `heapvis` command is executed, the addresses in the internal list of in-use addresses, the main arena, and the tcache are used to get a list of all chunks. Then chunks that are not part of the heap will be filtered, and the remaining chunks will be sorted. After that, all symbol-strings added by heapvis-symbol are resolved to addresses and mapped to the according chunks. Overlapping chunks will be pushed to a second (or third...) list, so that each list represents a column of the output. Finally, the output text is generated and printed.
When `heapvis-symbol` is called, each symbol is tested and then stored in an internal list of all added symbols. The symbols will be looked up every time `heapvis` is called, so if the symbol value changes, the new value is used.
