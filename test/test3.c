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
