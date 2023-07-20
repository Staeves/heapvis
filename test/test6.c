/*
 * This file is part of heapvis.
 *
 *  heapvis is free software: you can redistribute it and/or modify it under 
 *  the terms of the GNU General Public License as published by the 
 *  Free Software Foundation, either version 3 of the License, or 
 *  (at your option) any later version.
 *
 *  heapvis is distributed in the hope that it will be useful, but 
 *  WITHOUT ANY WARRANTY; without even the implied warranty of 
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
 *  General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License along 
 *  with heapvis. If not, see <https://www.gnu.org/licenses/>. 
 */

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
