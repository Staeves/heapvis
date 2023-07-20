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
