#include <stdlib.h>
#include <stdio.h>

int main(int argc, char** argv) {
	// loops in fd pointers
	// b at 24
	
	void* a[8];
	int i;

	for (i = 0; i < 8; i++) {
		a[i] = malloc(0x10);
		malloc(0x20);
	}
	for (i = 0; i < 8; i++) {
		free(a[i]);
	}
	
	//create a loop in the tcache chunks next pointers
	*((long*)(a[0])) = a[2];
	// and in the main arena
	*((long*)(a[7])) = a[7];

	// expect the chunks of a in tcache/main arena
	// each followed by a chunk of size 0x30

























}
