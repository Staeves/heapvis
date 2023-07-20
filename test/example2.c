#include <stdlib.h>
#include <stdio.h>

int main(int argc, char** argv) {
	void* a = malloc(0x20);
	void* b = a+0x10;
	*((long*)(b-0x8)) = 0x21;
	free(b);
	// breakpoint
}
