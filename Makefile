# For Cross Complie ENV.
# TOOLCHAINDIR=/home/ncoretti/openwrt/openwrt-buildsys/Code/staging_dir/toolchain-i386_gcc-4.4.3_glibc-2.6.1/usr/bin
# CC=$(TOOLCHAINDIR)/i486-openwrt-linux-gcc
# CXX=$(TOOLCHAINDIR)/i486-openwrt-linux-g++
# LD=$(TOOLCHAINDIR)/i486-openwrt-linux-ld
# AS=$(TOOLCHAINDIR)/i486-openwrt-linux-as

CFLAGS = -g

all: pipe_lat pipe_thr \
	unix_lat unix_thr \
	tcp_lat tcp_thr \
	tcp_local_lat tcp_remote_lat \
	shm

shm: shm.c
	$(CC) $(CFLAGS) shm.c -lrt  -o shm
	

	
run:
	./pipe_lat 100 10000
	./unix_lat 100 10000
	./tcp_lat 100 10000
	./pipe_thr 100 10000
	./unix_thr 100 10000
	./tcp_thr 100 10000

clean:
	rm -f *~ core
	rm -f pipe_lat pipe_thr 
	rm -f unix_lat unix_thr 
	rm -f tcp_lat tcp_thr 
	rm -f tcp_local_lat tcp_remote_lat
	rm -f shm 


CFLAGS = -g

all: pipe_lat pipe_thr \
	unix_lat unix_thr \
	tcp_lat tcp_thr \
	tcp_local_lat tcp_remote_lat \
	shm

shm: shm.c
	$(CC) $(CFLAGS) shm.c -lrt  -o shm
	

	
run:
	./tcp_lat 1024 10000
	./pipe_thr 1024 10000
	./unix_thr 1024 10000
	./tcp_thr 1024 10000

clean:
	rm -f *~ core
	rm -f pipe_lat pipe_thr 
	rm -f unix_lat unix_thr 
	rm -f tcp_lat tcp_thr 
	rm -f tcp_local_lat tcp_remote_lat
	rm -f shm 
