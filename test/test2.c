#include <stdlib.h>
#include <stdio.h>

int main(int argc, char** argv) {
	// tchache size corruption
	// b at 11, 15, 19, 23
	
	void *a = malloc(0x48);
	*((long*)(a-0x8)) = 0x71;

	// expeckt overlap with topchunk
	
	free(a);

	// expect same, but a is in tchache
	
	a = malloc(0x68);

	// expect a back in use
	
	*((long*)(a-0x8)) = 0x21;

	// expect gap between a and topchunk




























}
