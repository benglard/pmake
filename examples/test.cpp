#include <iostream>

void print() {
#ifdef TEST
  std::cout << "Hello world! Test!" << std::endl;
#else
  std::cout << "Hello world!" << std::endl;
#endif
}
