#include <stdlib.h>
#include <stdio.h>

int main(int argc, char** argv) {
	// tchache next pointer corruption to get one chunk twice
	// b at 18
	
	void *a = malloc(0x21);
	void *b = malloc(0x21);
	void *c = malloc(0x21);
	free(b);
	free(c);
	*((long*)(a)) = 0x00;
	*((long*)(c)) = (long) a;
	void *d = malloc(0x21);
	void *e = malloc(0x21);

	// expect a and e on top as same chunk
	// 	b is lost and now an empty gap
	// 	c is now d and after the gap from b
	// 	then the topchunk
	// 	everything is in use
	




























}
