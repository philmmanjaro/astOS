#!/usr/bin/python3

import sys
import subprocess

# TODO: the installer needs a proper rewrite

args = list(sys.argv)

def clear():
    subprocess.run("clear")

def to_uuid(part):
    uuid = str(subprocess.check_output(f"blkid -s UUID -o value {part}", shell=True))
    return uuid.replace("b'","").replace('"',"").replace("\\n'","")

def main(args):

    while True:
        clear()
        print("Welcome to the astOS installer!\n\n\n\n\n")
        print("Select installation profile:\n1. Minimal install - suitable for embedded devices or servers\n2. Desktop install (Gnome) - suitable for workstations\n3. Desktop install (KDE Plasma)\n4. Desktop install (MATE)")
        InstallProfile = str(input("> "))
        if InstallProfile == "1":
            DesktopInstall = 0
            break
        if InstallProfile == "2":
            DesktopInstall = 1
            break
        if InstallProfile == "3":
            DesktopInstall = 2
            break
        if InstallProfile == "4":
            DesktopInstall = 3
            break


    clear()
    while True:
        print("Select a timezone (type list to list):")
        zone = input("> ")
        if zone == "list":
            subprocess.run("ls /usr/share/zoneinfo | less")
        else:
            timezone = str(f"/usr/share/zoneinfo/{zone}")
            break

    clear()
    print("Enter hostname:")
    hostname = input("> ")

    subprocess.run("pacman -Syy --noconfirm archlinux-keyring")
    subprocess.run(f"mkfs.btrfs -f {args[1]}")

    if os.path.exists("/sys/firmware/efi"):
        efi = True
    else:
        efi = False

    subprocess.run(f"mount {args[1]} /mnt")
    btrdirs = ["@","@.snapshots","@home","@var","@etc","@boot"]
    mntdirs = ["",".snapshots","home","var","etc","boot"]

    for btrdir in btrdirs:
        subprocess.run(f"btrfs sub create /mnt/{btrdir}")

    subprocess.run(f"umount /mnt")

    for mntdir in mntdirs:
        subprocess.run(f"mkdir /mnt/{mntdir}")
        subprocess.run(f"mount {args[1]} -o subvol={btrdirs[mntdirs.index(mntdir)]},compress=zstd,noatime /mnt/{mntdir}")

    for i in ("tmp", "root"):
        subprocess.run(f"mkdir -p /mnt/{i}")
    for i in ("ast", "boot", "etc", "root", "rootfs", "tmp", "var"):
        subprocess.run(f"mkdir -p /mnt/.snapshots/{i}")

    if efi:
        subprocess.run("mkdir /mnt/boot/efi")
        subprocess.run(f"mount {args[3]} /mnt/boot/efi")

    excode = int(subprocess.run("pacstrap /mnt base linux linux-firmware nano python3 python-anytree bash dhcpcd arch-install-scripts btrfs-progs networkmanager grub"))
    if excode != 0:
        print("Failed to download packages!")
        sys.exit()

    if efi:
        excode = int(subprocess.run("pacstrap /mnt efibootmgr"))
        if excode != 0:
            print("Failed to download packages!")
            sys.exit()
            
            
    subprocess.run(f"echo 'UUID=\"{to_uuid(args[1])}\" / btrfs subvol=@,compress=zstd,noatime,ro 0 0' > /mnt/etc/fstab")
            
    for mntdir in mntdirs[1:]:
        subprocess.run(f"echo 'UUID=\"{to_uuid(args[1])}\" /{mntdir} btrfs subvol=@{mntdir},compress=zstd,noatime 0 0' >> /mnt/etc/fstab")

    if efi:
        subprocess.run(f"echo 'UUID=\"{to_uuid(args[3])}\" /boot/efi vfat umask=0077 0 2' >> /mnt/etc/fstab")

    subprocess.run("echo '/.snapshots/ast/root /root none bind 0 0' >> /mnt/etc/fstab")
    subprocess.run("echo '/.snapshots/ast/tmp /tmp none bind 0 0' >> /mnt/etc/fstab")

    astpart = to_uuid(args[1])

    subprocess.run(f"mkdir -p /mnt/usr/share/ast/db")
    subprocess.run(f"echo '0' > /mnt/usr/share/ast/snap")

    subprocess.run(f"echo 'NAME=\"astOS\"' > /mnt/etc/os-release")
    subprocess.run(f"echo 'PRETTY_NAME=\"astOS\"' >> /mnt/etc/os-release")
    subprocess.run(f"echo 'ID=astos' >> /mnt/etc/os-release")
    subprocess.run(f"echo 'BUILD_ID=rolling' >> /mnt/etc/os-release")
    subprocess.run(f"echo 'ANSI_COLOR=\"38;2;23;147;209\"' >> /mnt/etc/os-release")
    subprocess.run(f"echo 'HOME_URL=\"https://github.com/CuBeRJAN/astOS\"' >> /mnt/etc/os-release")
    subprocess.run(f"echo 'LOGO=astos-logo' >> /mnt/etc/os-release")
    subprocess.run(f"cp -r /mnt/var/lib/pacman/* /mnt/usr/share/ast/db")
    subprocess.run(f"sed -i s,\"#DBPath      = /var/lib/pacman/\",\"DBPath      = /usr/share/ast/db/\",g /mnt/etc/pacman.conf")
    subprocess.run(f"echo 'DISTRIB_ID=\"astOS\"' > /mnt/etc/lsb-release")
    subprocess.run(f"echo 'DISTRIB_RELEASE=\"rolling\"' >> /mnt/etc/lsb-release")
    subprocess.run(f"echo 'DISTRIB_DESCRIPTION=astOS' >> /mnt/etc/lsb-release")

    subprocess.run(f"arch-chroot /mnt ln -sf {timezone} /etc/localtime")
    subprocess.run("echo 'en_US UTF-8' >> /mnt/etc/locale.gen")
#    subprocess.run("sed -i s/'^#'// /mnt/etc/locale.gen")
#    subprocess.run("sed -i s/'^ '/'#'/ /mnt/etc/locale.gen")
    subprocess.run(f"arch-chroot /mnt locale-gen")
    subprocess.run(f"arch-chroot /mnt hwclock --systohc")
    subprocess.run(f"echo 'LANG=en_US.UTF-8' > /mnt/etc/locale.conf")
    subprocess.run(f"echo {hostname} > /mnt/etc/hostname")

    subprocess.run("sed -i '0,/@/{s,@,@.snapshots/rootfs/snapshot-tmp,}' /mnt/etc/fstab")
    subprocess.run("sed -i '0,/@etc/{s,@etc,@.snapshots/etc/etc-tmp,}' /mnt/etc/fstab")
#    subprocess.run("sed -i '0,/@var/{s,@var,@.snapshots/var/var-tmp,}' /mnt/etc/fstab")
    subprocess.run("sed -i '0,/@boot/{s,@boot,@.snapshots/boot/boot-tmp,}' /mnt/etc/fstab")
    subprocess.run("mkdir -p /mnt/.snapshots/ast/snapshots")

    subprocess.run("cp ./astpk.py /mnt/.snapshots/ast/ast")
    subprocess.run("arch-chroot /mnt chmod +x /.snapshots/ast/ast")
    subprocess.run("arch-chroot /mnt ln -s /.snapshots/ast /var/lib/ast")

    clear()
    if not DesktopInstall: # Skip asking for password if doing a desktop install, since root account will be locked anyway (sudo used instead)
        subprocess.run("arch-chroot /mnt passwd")
        while True:
            print("did your password set properly (y/n)?")
            reply = input("> ")
            if reply.casefold() == "y":
                break
            else:
                clear()
                subprocess.run("arch-chroot /mnt passwd")

    subprocess.run("arch-chroot /mnt systemctl enable NetworkManager")
    subprocess.run("echo {\\'name\\': \\'root\\', \\'children\\': [{\\'name\\': \\'0\\'}]} > /mnt/.snapshots/ast/fstree")

    if DesktopInstall:
        subprocess.run("echo {\\'name\\': \\'root\\', \\'children\\': [{\\'name\\': \\'0\\'},{\\'name\\': \\'1\\'}]} > /mnt/.snapshots/ast/fstree")
        subprocess.run(f"echo '{astpart}' > /mnt/.snapshots/ast/part")

    subprocess.run(f"arch-chroot /mnt sed -i s,Arch,astOS,g /etc/default/grub")
    subprocess.run(f"arch-chroot /mnt grub-install {args[2]}")
    subprocess.run(f"arch-chroot /mnt grub-mkconfig {args[2]} -o /boot/grub/grub.cfg")
    subprocess.run("sed -i '0,/subvol=@/{s,subvol=@,subvol=@.snapshots/rootfs/snapshot-tmp,g}' /mnt/boot/grub/grub.cfg")
    subprocess.run("arch-chroot /mnt ln -s /.snapshots/ast/ast /usr/local/sbin/ast")
    subprocess.run("btrfs sub snap -r /mnt /mnt/.snapshots/rootfs/snapshot-0")
    subprocess.run("btrfs sub create /mnt/.snapshots/etc/etc-tmp")
#    subprocess.run("btrfs sub create /mnt/.snapshots/var/var-tmp")
    subprocess.run("btrfs sub create /mnt/.snapshots/boot/boot-tmp")
#    subprocess.run("cp --reflink=auto -r /mnt/var/* /mnt/.snapshots/var/var-tmp")
#    for i in ("pacman", "systemd"):
#        subprocess.run(f"mkdir -p /mnt/.snapshots/var/var-tmp/lib/{i}")
 #   subprocess.run("cp --reflink=auto -r /mnt/var/lib/pacman/* /mnt/.snapshots/var/var-tmp/lib/pacman/")
 #   subprocess.run("cp --reflink=auto -r /mnt/var/lib/systemd/* /mnt/.snapshots/var/var-tmp/lib/systemd/")
    subprocess.run("cp --reflink=auto -r /mnt/boot/* /mnt/.snapshots/boot/boot-tmp")
    subprocess.run("cp --reflink=auto -r /mnt/etc/* /mnt/.snapshots/etc/etc-tmp")
 #   subprocess.run("btrfs sub snap -r /mnt/.snapshots/var/var-tmp /mnt/.snapshots/var/var-0")
    subprocess.run("btrfs sub snap -r /mnt/.snapshots/boot/boot-tmp /mnt/.snapshots/boot/boot-0")
    subprocess.run("btrfs sub snap -r /mnt/.snapshots/etc/etc-tmp /mnt/.snapshots/etc/etc-0")
    subprocess.run(f"echo '{astpart}' > /mnt/.snapshots/ast/part")

    if DesktopInstall == 1:
        subprocess.run(f"echo '1' > /mnt/usr/share/ast/snap")
        excode = int(subprocess.run("pacstrap /mnt flatpak gnome gnome-themes-extra gdm pipewire pipewire-pulse sudo"))
        if excode != 0:
            print("Failed to download packages!")
            sys.exit()
        clear()
        print("Enter username (all lowercase, max 8 letters)")
        username = input("> ")
        while True:
            print("did your set username properly (y/n)?")
            reply = input("> ")
            if reply.casefold() == "y":
                break
            else:
                clear()
                print("Enter username (all lowercase, max 8 letters)")
                username = input("> ")
        subprocess.run(f"arch-chroot /mnt useradd {username}")
        subprocess.run(f"arch-chroot /mnt passwd {username}")
        while True:
            print("did your password set properly (y/n)?")
            reply = input("> ")
            if reply.casefold() == "y":
                break
            else:
                clear()
                subprocess.run(f"arch-chroot /mnt passwd {username}")
        subprocess.run(f"arch-chroot /mnt usermod -aG audio,input,video,wheel {username}")
        subprocess.run(f"arch-chroot /mnt passwd -l root")
        subprocess.run(f"chmod +w /mnt/etc/sudoers")
        subprocess.run(f"echo '%wheel ALL=(ALL:ALL) ALL' >> /mnt/etc/sudoers")
        subprocess.run(f"chmod -w /mnt/etc/sudoers")
        subprocess.run(f"arch-chroot /mnt mkdir /home/{username}")
        subprocess.run(f"echo 'export XDG_RUNTIME_DIR=\"/run/user/1000\"' >> /home/{username}/.bashrc")
        subprocess.run(f"arch-chroot /mnt chown -R {username} /home/{username}")
        subprocess.run(f"arch-chroot /mnt systemctl enable gdm")
        subprocess.run(f"cp -r /mnt/var/lib/pacman/* /mnt/usr/share/ast/db")
        subprocess.run("btrfs sub snap -r /mnt /mnt/.snapshots/rootfs/snapshot-1")
        subprocess.run("btrfs sub del /mnt/.snapshots/etc/etc-tmp")
 #       subprocess.run("btrfs sub del /mnt/.snapshots/var/var-tmp")
        subprocess.run("btrfs sub del /mnt/.snapshots/boot/boot-tmp")
        subprocess.run("btrfs sub create /mnt/.snapshots/etc/etc-tmp")
 #       subprocess.run("btrfs sub create /mnt/.snapshots/var/var-tmp")
        subprocess.run("btrfs sub create /mnt/.snapshots/boot/boot-tmp")
#        subprocess.run("cp --reflink=auto -r /mnt/var/* /mnt/.snapshots/var/var-tmp")
 #       for i in ("pacman", "systemd"):
 #           subprocess.run(f"mkdir -p /mnt/.snapshots/var/var-tmp/lib/{i}")
 #       subprocess.run("cp --reflink=auto -r /mnt/var/lib/pacman/* /mnt/.snapshots/var/var-tmp/lib/pacman/")
 #       subprocess.run("cp --reflink=auto -r /mnt/var/lib/systemd/* /mnt/.snapshots/var/var-tmp/lib/systemd/")
        subprocess.run("cp --reflink=auto -r /mnt/boot/* /mnt/.snapshots/boot/boot-tmp")
        subprocess.run("cp --reflink=auto -r /mnt/etc/* /mnt/.snapshots/etc/etc-tmp")
 #       subprocess.run("btrfs sub snap -r /mnt/.snapshots/var/var-tmp /mnt/.snapshots/var/var-1")
        subprocess.run("btrfs sub snap -r /mnt/.snapshots/boot/boot-tmp /mnt/.snapshots/boot/boot-1")
        subprocess.run("btrfs sub snap -r /mnt/.snapshots/etc/etc-tmp /mnt/.snapshots/etc/etc-1")
        subprocess.run("btrfs sub snap /mnt/.snapshots/rootfs/snapshot-1 /mnt/.snapshots/rootfs/snapshot-tmp")
        subprocess.run("arch-chroot /mnt btrfs sub set-default /.snapshots/rootfs/snapshot-tmp")

    elif DesktopInstall == 2:
        subprocess.run(f"echo '1' > /mnt/usr/share/ast/snap")
        excode = int(subprocess.run("pacstrap /mnt flatpak plasma xorg konsole dolphin sddm pipewire pipewire-pulse sudo"))
        if excode != 0:
            print("Failed to download packages!")
            sys.exit()
        clear()
        print("Enter username (all lowercase, max 8 letters)")
        username = input("> ")
        while True:
            print("did your set username properly (y/n)?")
            reply = input("> ")
            if reply.casefold() == "y":
                break
            else:
                clear()
                print("Enter username (all lowercase, max 8 letters)")
                username = input("> ")
        subprocess.run(f"arch-chroot /mnt useradd {username}")
        subprocess.run(f"arch-chroot /mnt passwd {username}")
        while True:
            print("did your password set properly (y/n)?")
            reply = input("> ")
            if reply.casefold() == "y":
                break
            else:
                clear()
                subprocess.run(f"arch-chroot /mnt passwd {username}")
        subprocess.run(f"arch-chroot /mnt usermod -aG audio,input,video,wheel {username}")
        subprocess.run(f"arch-chroot /mnt passwd -l root")
        subprocess.run(f"chmod +w /mnt/etc/sudoers")
        subprocess.run(f"echo '%wheel ALL=(ALL:ALL) ALL' >> /mnt/etc/sudoers")
        subprocess.run(f"echo '[Theme]' > /mnt/etc/sddm.conf")
        subprocess.run(f"echo 'Current=breeze' >> /mnt/etc/sddm.conf")
        subprocess.run(f"chmod -w /mnt/etc/sudoers")
        subprocess.run(f"arch-chroot /mnt mkdir /home/{username}")
        subprocess.run(f"echo 'export XDG_RUNTIME_DIR=\"/run/user/1000\"' >> /home/{username}/.bashrc")
        subprocess.run(f"arch-chroot /mnt chown -R {username} /home/{username}")
        subprocess.run(f"arch-chroot /mnt systemctl enable sddm")
        subprocess.run(f"cp -r /mnt/var/lib/pacman/* /mnt/usr/share/ast/db")
        subprocess.run("btrfs sub snap -r /mnt /mnt/.snapshots/rootfs/snapshot-1")
        subprocess.run("btrfs sub del /mnt/.snapshots/etc/etc-tmp")
  #      subprocess.run("btrfs sub del /mnt/.snapshots/var/var-tmp")
        subprocess.run("btrfs sub del /mnt/.snapshots/boot/boot-tmp")
        subprocess.run("btrfs sub create /mnt/.snapshots/etc/etc-tmp")
  #      subprocess.run("btrfs sub create /mnt/.snapshots/var/var-tmp")
        subprocess.run("btrfs sub create /mnt/.snapshots/boot/boot-tmp")
#        subprocess.run("cp --reflink=auto -r /mnt/var/* /mnt/.snapshots/var/var-tmp")
#        for i in ("pacman", "systemd"):
#            subprocess.run(f"mkdir -p /mnt/.snapshots/var/var-tmp/lib/{i}")
  #      subprocess.run("cp --reflink=auto -r /mnt/var/lib/pacman/* /mnt/.snapshots/var/var-tmp/lib/pacman/")
  #      subprocess.run("cp --reflink=auto -r /mnt/var/lib/systemd/* /mnt/.snapshots/var/var-tmp/lib/systemd/")
        subprocess.run("cp --reflink=auto -r /mnt/boot/* /mnt/.snapshots/boot/boot-tmp")
        subprocess.run("cp --reflink=auto -r /mnt/etc/* /mnt/.snapshots/etc/etc-tmp")
   #     subprocess.run("btrfs sub snap -r /mnt/.snapshots/var/var-tmp /mnt/.snapshots/var/var-1")
        subprocess.run("btrfs sub snap -r /mnt/.snapshots/boot/boot-tmp /mnt/.snapshots/boot/boot-1")
        subprocess.run("btrfs sub snap -r /mnt/.snapshots/etc/etc-tmp /mnt/.snapshots/etc/etc-1")
        subprocess.run("btrfs sub snap /mnt/.snapshots/rootfs/snapshot-1 /mnt/.snapshots/rootfs/snapshot-tmp")
        subprocess.run("arch-chroot /mnt btrfs sub set-default /.snapshots/rootfs/snapshot-tmp")

    elif DesktopInstall == 3:
        subprocess.run(f"echo '1' > /mnt/usr/share/ast/snap")
        excode = int(subprocess.run("pacstrap /mnt flatpak mate pluma caja mate-terminal gdm pipewire pipewire-pulse sudo ttf-dejavu mate-extra"))
        if excode != 0:
            print("Failed to download packages!")
            sys.exit()
        clear()
        print("Enter username (all lowercase, max 8 letters)")
        username = input("> ")
        while True:
            print("did your set username properly (y/n)?")
            reply = input("> ")
            if reply.casefold() == "y":
                break
            else:
                clear()
                print("Enter username (all lowercase, max 8 letters)")
                username = input("> ")
        subprocess.run(f"arch-chroot /mnt useradd {username}")
        subprocess.run(f"arch-chroot /mnt passwd {username}")
        while True:
            print("did your password set properly (y/n)?")
            reply = input("> ")
            if reply.casefold() == "y":
                break
            else:
                clear()
                subprocess.run(f"arch-chroot /mnt passwd {username}")
        subprocess.run(f"arch-chroot /mnt usermod -aG audio,input,video,wheel {username}")
        subprocess.run(f"arch-chroot /mnt passwd -l root")
        subprocess.run(f"chmod +w /mnt/etc/sudoers")
        subprocess.run(f"echo '%wheel ALL=(ALL:ALL) ALL' >> /mnt/etc/sudoers")
        subprocess.run(f"chmod -w /mnt/etc/sudoers")
        subprocess.run(f"arch-chroot /mnt mkdir /home/{username}")
        subprocess.run(f"echo 'export XDG_RUNTIME_DIR=\"/run/user/1000\"' >> /home/{username}/.bashrc")
        subprocess.run(f"arch-chroot /mnt chown -R {username} /home/{username}")
        subprocess.run(f"arch-chroot /mnt systemctl enable gdm")
        subprocess.run(f"cp -r /mnt/var/lib/pacman/* /mnt/usr/share/ast/db")
        subprocess.run("btrfs sub snap -r /mnt /mnt/.snapshots/rootfs/snapshot-1")
        subprocess.run("btrfs sub del /mnt/.snapshots/etc/etc-tmp")
  #      subprocess.run("btrfs sub del /mnt/.snapshots/var/var-tmp")
        subprocess.run("btrfs sub del /mnt/.snapshots/boot/boot-tmp")
        subprocess.run("btrfs sub create /mnt/.snapshots/etc/etc-tmp")
  #      subprocess.run("btrfs sub create /mnt/.snapshots/var/var-tmp")
        subprocess.run("btrfs sub create /mnt/.snapshots/boot/boot-tmp")
#        subprocess.run("cp --reflink=auto -r /mnt/var/* /mnt/.snapshots/var/var-tmp")
#        for i in ("pacman", "systemd"):
#            subprocess.run(f"mkdir -p /mnt/.snapshots/var/var-tmp/lib/{i}")
  #      subprocess.run("cp --reflink=auto -r /mnt/var/lib/pacman/* /mnt/.snapshots/var/var-tmp/lib/pacman/")
  #      subprocess.run("cp --reflink=auto -r /mnt/var/lib/systemd/* /mnt/.snapshots/var/var-tmp/lib/systemd/")
        subprocess.run("cp --reflink=auto -r /mnt/boot/* /mnt/.snapshots/boot/boot-tmp")
        subprocess.run("cp --reflink=auto -r /mnt/etc/* /mnt/.snapshots/etc/etc-tmp")
   #     subprocess.run("btrfs sub snap -r /mnt/.snapshots/var/var-tmp /mnt/.snapshots/var/var-1")
        subprocess.run("btrfs sub snap -r /mnt/.snapshots/boot/boot-tmp /mnt/.snapshots/boot/boot-1")
        subprocess.run("btrfs sub snap -r /mnt/.snapshots/etc/etc-tmp /mnt/.snapshots/etc/etc-1")
        subprocess.run("btrfs sub snap /mnt/.snapshots/rootfs/snapshot-1 /mnt/.snapshots/rootfs/snapshot-tmp")
        subprocess.run("arch-chroot /mnt btrfs sub set-default /.snapshots/rootfs/snapshot-tmp")

    else:
        subprocess.run("btrfs sub snap /mnt/.snapshots/rootfs/snapshot-0 /mnt/.snapshots/rootfs/snapshot-tmp")
        subprocess.run("arch-chroot /mnt btrfs sub set-default /.snapshots/rootfs/snapshot-tmp")

    subprocess.run("cp -r /mnt/root/. /mnt/.snapshots/root/")
    subprocess.run("cp -r /mnt/tmp/. /mnt/.snapshots/tmp/")
    subprocess.run("rm -rf /mnt/root/*")
    subprocess.run("rm -rf /mnt/tmp/*")
#    subprocess.run("umount /mnt/var")

    if efi:
        subprocess.run("umount /mnt/boot/efi")

    subprocess.run("umount /mnt/boot")
#    subprocess.run("mkdir /mnt/.snapshots/var/var-tmp")
#    subprocess.run("mkdir /mnt/.snapshots/boot/boot-tmp")
#    subprocess.run(f"mount {args[1]} -o subvol=@var,compress=zstd,noatime /mnt/.snapshots/var/var-tmp")
    subprocess.run(f"mount {args[1]} -o subvol=@boot,compress=zstd,noatime /mnt/.snapshots/boot/boot-tmp")
#    subprocess.run("cp --reflink=auto -r /mnt/.snapshots/var/var-tmp/* /mnt/var")
    subprocess.run("cp --reflink=auto -r /mnt/.snapshots/boot/boot-tmp/* /mnt/boot")
    subprocess.run("umount /mnt/etc")
#    subprocess.run("mkdir /mnt/.snapshots/etc/etc-tmp")
    subprocess.run(f"mount {args[1]} -o subvol=@etc,compress=zstd,noatime /mnt/.snapshots/etc/etc-tmp")
    subprocess.run("cp --reflink=auto -r /mnt/.snapshots/etc/etc-tmp/* /mnt/etc")

    if DesktopInstall:
        subprocess.run("cp --reflink=auto -r /mnt/.snapshots/etc/etc-1/* /mnt/.snapshots/rootfs/snapshot-tmp/etc")
   #     subprocess.run("cp --reflink=auto -r /mnt/.snapshots/var/var-1/* /mnt/.snapshots/rootfs/snapshot-tmp/var")
        subprocess.run("cp --reflink=auto -r /mnt/.snapshots/boot/boot-1/* /mnt/.snapshots/rootfs/snapshot-tmp/boot")
    else:
        subprocess.run("cp --reflink=auto -r /mnt/.snapshots/etc/etc-0/* /mnt/.snapshots/rootfs/snapshot-tmp/etc")
    #    subprocess.run("cp --reflink=auto -r /mnt/.snapshots/var/var-0/* /mnt/.snapshots/rootfs/snapshot-tmp/var")
        subprocess.run("cp --reflink=auto -r /mnt/.snapshots/boot/boot-0/* /mnt/.snapshots/rootfs/snapshot-tmp/boot")

    subprocess.run("umount -R /mnt")
    subprocess.run(f"mount {args[1]} -o subvolid=0 /mnt")
    subprocess.run("btrfs sub del /mnt/@")
    subprocess.run("umount -R /mnt")
    clear()
    print("Installation complete")
    print("You can reboot now :)")

main(args)

