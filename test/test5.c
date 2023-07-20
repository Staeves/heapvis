#include <stdlib.h>
#include <stdio.h>

int main(int argc, char** argv) {
	// all sizes
	// b at 17, 27, 37
	int i;
	int s;
	void *a[9];
	void *block;

	for (s = 0; s < 0x40; s++) {
		printf("0x%x\n", s);
		for (i = 0; i < 0x9; i++) {
			a[i] = malloc(s*0x10);
		}
		block = malloc(0x18);

		// expect 9 chunks of size s*0x10
		// 	at the bottem of the output only 
		// 	followed by the 0x20 block chunk and the topchunk
		
		for(i = 0; i < 0x8; i++) {
			free(a[i]);
		}

		// expect the 9 chunks to be (in that order)
		// 7x in tcache
		// 1x in arena
		// 1x in use
		// 0x20 block chunk
		// top chunk
		
		free(a[0x8]);

		// expect the 9 now:
		// 7x in tcache
		// 2x in arena or in case of smallbin 1 consolidated
		// 0x20 block chunk
		// top chunk

		for (i = 0; i < 0x9; i++) {
			malloc(s*0x10);		// nothing left for reuse
		}
	}























}
