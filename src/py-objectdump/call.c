#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>

uint8_t* create_function(int size, const uint8_t* bytes) {
  // On Mac OS X and other BSD-based UNIX derivatives,
  // "MAP_ANONYMOUS" is called "MAP_ANON".
  uint8_t *buf = mmap(NULL, size,
                      PROT_EXEC | PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANON, -1, 0);
  memcpy(buf, bytes, size);
  return buf;
}

int main(int argc, char *argv[]) {
  int (*f)(void) =
    (int (*)(void)) create_function(6,
      (uint8_t[6]) { 0xb8, 0x2a, 0x00, 0x00, 0x00, 0xc3 }
    );
  
  printf("return is %d\n", f());
  return 0;
}
