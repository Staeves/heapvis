#include <stdlib.h>
#include <stdio.h>

int main(int argc, char** argv) {
	void* a = malloc(0x20);
	void* b = malloc(0x20);
	free(a);
	// breakpoint
}
