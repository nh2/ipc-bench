# For Cross Complie ENV.
# TOOLCHAINDIR=/home/ncoretti/openwrt/openwrt-buildsys/Code/staging_dir/toolchain-i386_gcc-4.4.3_glibc-2.6.1/usr/bin
# CC=$(TOOLCHAINDIR)/i486-openwrt-linux-gcc
# CXX=$(TOOLCHAINDIR)/i486-openwrt-linux-g++
# LD=$(TOOLCHAINDIR)/i486-openwrt-linux-ld
# AS=$(TOOLCHAINDIR)/i486-openwrt-linux-as

# Vars for deployment
TARGET_HOST =  192.168.0.12
SSH_KEYFILE = /home/ncoretti/.ssh/vigem-cca_id_rsa2048
DEPLOY_DIR = /tmp/ipc-bench

CFLAGS = -g

all: pipe_lat pipe_thr \
	unix_lat unix_thr \
	tcp_lat tcp_thr \
	tcp_local_lat tcp_remote_lat \
	named_pipe_thr \
	msgq_thr \
	shm

shm: shm.c
	$(CC) $(CFLAGS) shm.c -lrt  -o shm
	

	
run_lat:
	./pipe_lat 100 10000
	./unix_lat 100 10000
	./tcp_lat 100 10000

run_thr:
	./pipe_thr 100 10000
	./named_pipe_thr 100 10000
	./msgq_thr 100 10000
	./unix_thr 100 10000
	./tcp_thr 100 10000

deploy: all
	ssh -i $(SSH_KEYFILE) root@$(TARGET_HOST) "mkdir $(DEPLOY_DIR)"
	scp -i $(SSH_KEYFILE) pipe_thr root@$(TARGET_HOST):$(DEPLOY_DIR)/pipe_thr
	scp -i $(SSH_KEYFILE) named_pipe_thr root@$(TARGET_HOST):$(DEPLOY_DIR)/named_pipe_thr
	scp -i $(SSH_KEYFILE) msgq_thr root@$(TARGET_HOST):$(DEPLOY_DIR)/msgq_thr
	scp -i $(SSH_KEYFILE) unix_thr root@$(TARGET_HOST):$(DEPLOY_DIR)/unix_thr
	scp -i $(SSH_KEYFILE) tcp_thr root@$(TARGET_HOST):$(DEPLOY_DIR)/tcp_thr
	scp -i $(SSH_KEYFILE) ipc_bench.py root@$(TARGET_HOST):$(DEPLOY_DIR)/ipc_bench.py

clean:
	rm -f *~ core
	rm -f pipe_lat pipe_thr 
	rm -f named_pipe_thr
	rm -f msgq_thr
	rm -f unix_lat unix_thr 
	rm -f tcp_lat tcp_thr 
	rm -f tcp_local_lat tcp_remote_lat
	rm -f shm 
	rm -f ipc_bench_*
	rm -f *.tar.gz
