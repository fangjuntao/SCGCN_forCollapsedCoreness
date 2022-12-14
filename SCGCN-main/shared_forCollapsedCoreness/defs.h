#ifndef CORE_DEFS_H_
#define CORE_DEFS_H_

#include <cstdio>
#include <cstdlib>

#ifdef __GNUC__
#define likely(x) __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#else
#define likely(x) (x)
#define unlikely(x) (x)
#endif

#define ASSERT(truth) \
    if (!(truth)) { \
      printf("\x1b[1;31mASSERT\x1b[0m, LINE:%d, FILE:%s\n", \
             __LINE__, __FILE__); \
      exit(EXIT_FAILURE); \
    } else

#define ASSERT_INFO(truth, info) \
    if (!(truth)) { \
      printf("\x1b[1;31mASSERT\x1b[0m, LINE:%d, FILE:%s\n", \
             __LINE__, __FILE__); \
      printf("\x1b[1;32mINFO\x1b[0m: %s\n", info); \
      exit(EXIT_FAILURE); \
    } else

#define ERROR(msg, to_exit) \
    if (true) { \
      printf("\x1b[1;31mERROR\x1b[0m: %s\n", msg); \
      if (to_exit) { \
        exit(EXIT_FAILURE); \
      } \
    } else

#endif