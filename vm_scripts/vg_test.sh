#!/bin/bash

# install deps
apt-get update ; apt-get install -y lvm2 xfsprogs

# do lvm work
DOKdev=/dev/vdc
mkdir /mnt/storage

while [ -z `fdisk -l $DOKdev 2>&1 | grep Disk` ]
do
    sleep 3
    echo "waiting for $DOKdev ..."
done

echo "======== Creating physical volume $DOKdev ========"
pvcreate $DOKdev
echo ""
echo "======== Creating volume group vg ========"
vgcreate vg-foobar $DOKdev
echo ""
echo "======== Creating logical volume lvol0 ========"
lvcreate --extents 90%VG --name lvol0 --stripes 1 --stripesize 256 vg-foobar

echo ""
echo "======== Mounting lvol0 on /mnt/storage ========"
mkfs.ext3 /dev/vg-foobar/lvol0
mount -o noatime /dev/vg-foobar/lvol0 /mnt/storage

echo ""
echo "======== Creating logical volume blockdevice_lvm_snapshot ========="
lvcreate --extents 100%FREE --name blockdevice_lvm_snapshot --snapshot /dev/vg-foobar/lvol0

echo ""
echo "======== Removing lvm_snapshot ==============="
lvremove --force /dev/vg-foobar/blockdevice_lvm_snapshot
