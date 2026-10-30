systemctl stop docker
e2fsck -fy /dockerimages/ignite_vfs.ext4
resize2fs /dockerimages/ignite_vfs.ext4 10G
mount /dockerimages/ignite_vfs.ext4 /var/lib/docker
systemctl start docker
