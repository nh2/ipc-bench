/* 
    Measure throughput of IPC using named pipes


    Copyright (c) 2012 Nicola Coretti <nico.coretti@googlemail.com>

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
*/


#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>


int main(int argc, char *argv[])
{
  const char* fifo = "/tmp/fifotest";

  int size;
  char *buf;
  int64_t count, i, delta;
  struct timeval start, stop;

  if (argc != 3) {
    printf ("usage: named_pipe_thr <message-size> <message-count>\n");
    exit(1);
  }

  size = atoi(argv[1]);
  count = atol(argv[2]);

  buf = malloc(size);
  if (buf == NULL) {
    perror("malloc");
    exit(1);
  }

  printf("message size: %i octets\n", size);
  printf("message count: %lli\n", count);

  unlink(fifo);
  if (mkfifo(fifo, S_IWUSR | S_IRUSR | S_IRGRP |  S_IROTH) == -1) {
    perror("named-pipe");
    exit(1);
  }

  if (!fork()) {  
    /* child */
    int fd_r;

    if ((fd_r = open(fifo, O_RDONLY)) == -1) {
        perror("opening fifo for reading");
        exit(1);
    } 

    for (i = 0; i < count; i++) {      
      if (read(fd_r, buf, size) != size) {
        perror("read");
        exit(1);
      }
    }
  } else { 
    /* parent */
    int fd_w;

    if ((fd_w = open(fifo, O_WRONLY)) == -1) {
        perror("opening fifo for writing");
        exit(1);
    } 

    gettimeofday(&start, NULL);

    for (i = 0; i < count; i++) {
      if (write(fd_w, buf, size) != size) {
        perror("write");
        exit(1);
      }
    }

    gettimeofday(&stop, NULL);

    delta = ((stop.tv_sec - start.tv_sec) * (int64_t) 1e6 +
	     stop.tv_usec - start.tv_usec);

    printf("average throughput: %lli msg/s\n", (count * (int64_t) 1e6) / delta);
    printf("average throughput: %lli Mb/s\n", (((count * (int64_t) 1e6) / delta) * size * 8) / (int64_t) 1e6);
  }
  
  return 0;
}
