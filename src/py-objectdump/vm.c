#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>

uint8_t* create_function(char* name) {
  int size, in;
  
  printf("size %s = ", name);
  scanf("%d", &size);
  uint8_t *buf = mmap(NULL, size, PROT_EXEC | PROT_READ | PROT_WRITE,
                                  MAP_PRIVATE | MAP_ANON, -1, 0);
  printf("buffer for %s starts at %p\n", name, buf);
  for(int i=0; i<size; i++) {
    scanf("%x", &in);
    buf[i] = (uint8_t)in;
  }
  return buf;
}

int main(int argc, char *argv[]) {
  int (*f_a)(void)       = (int (*)(void)) create_function("a");
  printf("return of a is %d\n", f_a());

  int (*f_b)(void)       = (int (*)(void)) create_function("b");
  printf("return of b is %d\n", f_b());
  
  int (*f_mul_a_b)(void) = (int (*)(void)) create_function("mul_a_b");
  printf("return of mu_a_b is %d\n", f_mul_a_b());

  return 0;
}
