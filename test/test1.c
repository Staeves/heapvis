#include <stdlib.h>
#include <stdio.h>

int main(int argc, char** argv) {
	// a gap in memory
	// b at 22
	void* a = malloc(0x70);
	void* b = a+0x20;
	void* c = a+0x40;
	void* d = malloc(0x70);
	void* e = d+0x40;

	*((long*)(b-0x8)) = 0x51;
	*((long*)(c-0x8)) = 0x101;
	*((long*)(e-0x8)) = 0x51;
	
	free(b);
	free(c);
	free(e);

	// expect everything in tcache
	// 	a b and c start overlapping in that order 
	//	b ends then a
	//	d starts behind a
	//	e starts within d
	//	after d starts the topchunk
	//	after the beginning of the topchunk end e then c
/* e.g.
 0x5578fadb4290 ######################                    #                    #
 0x5578fadb42b0 # flags: 0 0 1       ######################                    #
 0x5578fadb42d0 # in use             # flags: 0 0 1       ######################
                # size: 0x80         # in tchache         # flags: 0 0 1       #
                # fd: 0x0            # size: 0x50         # in tchache         #
                #                    # fd: 0x0            # size: 0x100        #
 0x5578fadb4300 #                    ###################### fd: 0x0            #
 0x5578fadb4310 ######################                    #                    #
 0x5578fadb4350 # flags: 0 0 1       ######################                    #
                # in use             # flags: 0 0 1       #                    #
                # size: 0x80         # in tchache         #                    #
                # fd: 0x5578fadb42a0 # size: 0x50         #                    #
 0x5578fadb4390 ###################### fd: 0x5578fadb42c0 #                    #
 0x5578fadb43a0 # flags: 0 0 1       ######################                    #
 0x5578fadb43d0 # in the arena       #                    ######################
                # size: 0x20c70      #                    #                    #
                # fd: 0x0            #                    #                    #
                # bw: 0x0            #                    #                    #
		# TOP CHUNK          #                    #                    #
 0x5578fadd5000 ######################                    #                    #
*/



























}
