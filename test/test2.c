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
