/* 
    Measure throughput of IPC using  message queues


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
#include <sys/ipc.h>
#include <sys/msg.h>
#include <unistd.h>

#ifndef MSGMAX
#define MSGMAX 8192
#endif

int main(int argc, char *argv[])
{

    // -- Setup --
    int size;
    char *buf;
    int64_t count, i, delta;
    struct timeval start, stop;

    if (argc != 3) {
        printf ("usage: named_pipe_thr <message-size> <message-count>\n");
        exit(EXIT_FAILURE);
    }
    size = atoi(argv[1]);
    if (size > MSGMAX) {
        printf("message size is to large.\n");
        printf("max message size [%i] Bytes\n", MSGMAX); 
        exit(EXIT_FAILURE);
    }
    count = atol(argv[2]);

    struct test_msgbuf {
        long mtype;
        char mtext[size];
    };

    buf = malloc(size);
    if (buf == NULL) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    printf("message size: %i octets\n", size);
    printf("message count: %lli\n", count);

    key_t key;
    int msqid;
    if ((key = ftok(".", "i")) == -1) {
        perror("ftok");
        exit(EXIT_FAILURE);  
    }
    if ((msqid = msgget(key, 0666 | IPC_CREAT)) == -1) {
        perror("msgget");
        exit(EXIT_FAILURE);
    }
 
    
    // -- Test --
    if (!fork()) {  
        /* child */
        struct test_msgbuf msg;
        for (i = 0; i < count; i++) {      
            if (msgrcv(msqid, &msg, size, 1, 0) == -1) {
                perror("msgrcv");
                exit(EXIT_FAILURE);
            }
        }
    } 
    else { 
        
        /* parent */
        struct test_msgbuf msg;
        msg.mtype = 1;

        gettimeofday(&start, NULL);

        for (i = 0; i < count; i++) {
            if (msgsnd(msqid, &msg, size, 0) == -1) {
                perror("msgsnd");
                exit(EXIT_FAILURE);
            }
    }

    wait();
    gettimeofday(&stop, NULL);

    delta = ((stop.tv_sec - start.tv_sec) * (int64_t) 1e6 +
	     stop.tv_usec - start.tv_usec);

    printf("average throughput: %lli msg/s\n", (count * (int64_t) 1e6) / delta);
    printf("average throughput: %lli Mb/s\n", (((count * (int64_t) 1e6) / delta) * size * 8) / (int64_t) 1e6);
  }
  
  return 0;
}
