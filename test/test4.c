#include <stdlib.h>
#include <stdio.h>

int main(int argc, char** argv) {
	// smallbin consolidation
	// b at 25
	
	void *a = malloc(0x88);
	void *b = malloc(0x88);
	void *filler[7];	// to fill the tcache

	for (int i = 0; i < 7; i++) {
		filler[i] = malloc(0x88);
	}
	for (int i = 0; i < 7; i++) {
		free(filler[i]);
	}

	*((long*)(b-0x8)) = 0x90;	// overwrite prev in use
	*((long*)(b-0x10)) = 0x90;	// prevsize
	*((long*)(a)) = (long) (a-0x10);
	*((long*)(a+0x8)) = (long)(a-0x10);
	free(b);

	// expect a in use and the consolidation of a and b in the arena
	// 	then behind the consolidation the filler chunks in the 
	// 	tcache
	// 	and finaly the topchunk




























}
