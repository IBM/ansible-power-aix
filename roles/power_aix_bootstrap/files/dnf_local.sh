#!/bin/sh
# This scripts downloads the rpm.rte & dnf_bundle.tar
# rpm.rte-4.13.0.x which is a prequisite for dnf.
# dnf_bundle.tar contains dnf and its dependent packages.
# This script checks if any of the package from dnf_bundle is
# already installed and then installs the packages accordingly.

export LANG=C

# Check if we are running this as the root user.
if [ "$(id -u)" != "0" ]
then
    echo "This script must be run as root."
    exit 1
fi


# First check the AIX version.
oslvl=$(/usr/bin/oslevel)
aix_ver=$(/usr/bin/lslpp -qLc bos.rte | /usr/bin/awk -F':' '{print $3}')
af1=$(echo "$aix_ver" | /usr/bin/cut -d"." -f1)
af2=$(echo "$aix_ver" | /usr/bin/cut -d"." -f2)
af3=$(echo "$aix_ver" | /usr/bin/cut -d"." -f3)
if [ "$oslvl" = "7.1.0.0" ]
then
    if [ "$af1" -lt 7 ] || [ "$af2" -lt 1 ] || [ "$af3" -lt 3 ]
    then
        echo "dnf and dependencies can be installed on AIX 7.1.3 and higher versions."
        exit 1
    fi
else
    if [ "$af1" -lt 7 ] || [ "$af2" -lt 1 ]
    then
         echo "dnf and dependencies can be installed on AIX 7.1.3 and higher versions."
         exit 1
     fi
fi

# Check if yum3 is installed.
yum3_instd=0

prog=${0##*/}
yum4=2 # Install yum4

usage() {
    print >&2 "Usage: $prog <mount path or tar extraction path>

      mount path should be Absolute path where the AIX Toolbox iso image is
      being mounted or the path where AIX Toolbox tar file has been extracted."
    exit 1
}

if [ $# -ne 2 ]
then
    usage
    exit 1
fi

mnt_path=$1
if [ ! -e "$mnt_path" ]
then
    echo " path $mnt_path doesn't exists."
    echo " Please check the path and retry again."
    exit 1
fi

bundle_path=$2
if [ ! -e "$bundle_path" ]
then
    echo " path $bundle_path doesn't exists."
    echo " Please check the path and retry again."
    exit 1
fi

# Verify if few more paths of the iso/tar exists within mnt path.
if [ ! -e "${mnt_path}/AIX_Toolbox" ] || [ ! -e "${mnt_path}/AIX_Toolbox_noarch" ]
then
    echo "Some of required paths like AIX_Toolbox and AIX_Toolbox_noarch"
    echo "don't exists in the $mnt_path path."
    exit 1
fi

# Check openssl version.
print_openssl_err() {
    echo "Please install openssl 1.1.x and higher version."
    echo "You can download and install latest openssl from AIX web download site"
    echo "https://www-01.ibm.com/marketing/iwm/platform/mrs/assets?source=aixbp"
    exit 1
}
ssl_ver=$(lslpp -Lc openssl.base | /usr/bin/awk 'FNR==2' | /usr/bin/awk -F':' '{print $3}')
f1=$(echo "$ssl_ver" | /usr/bin/cut -d"." -f1)
f2=$(echo "$ssl_ver" | /usr/bin/cut -d"." -f2)
#f3=$(echo "$ssl_ver" | /usr/bin/cut -d"." -f3)
#f4=$(echo "$ssl_ver" | /usr/bin/cut -d"." -f4)

if [ "$f1" -lt 1 ] || { [ "$f1" -eq 1 ] && [ "$f2" -lt 1 ]; }; then
    print_openssl_err
fi

oslvl=$(/usr/bin/oslevel)
aix_730_plus=0
os_f1=$(echo "$oslvl" | /usr/bin/cut -d"." -f1)
os_f2=$(echo "$oslvl" | /usr/bin/cut -d"." -f2)
os_f3=$(echo "$oslvl" | /usr/bin/cut -d"." -f3)
os_f4=$(echo "$oslvl" | /usr/bin/cut -d"." -f4)

if [ "$os_f1" -ge 7 ] && [ "$os_f2" -ge 3 ] && [ "$os_f3" -ge 0 ] && [ "$os_f4" -ge 0 ]
then
    aix_730_plus=1
fi

# Check if /tmp has enough space to download rpm.rte & dnf_bundle
# and size for extracting rpm packages.
# For 71_72 bundle it requires around 340 MB of free space.
# 170M for bundle which includes rpm.rte (40M) and rpm packages (130M).
# rpm packages extracted.

if [ $aix_730_plus -eq 1 ]
then
    total_req=$(echo "(512)" | bc)
    tmp_free=$(/usr/bin/df -m /tmp | /usr/bin/sed -e /Filesystem/d | /usr/bin/awk '{print $3}')

    if [ "$tmp_free" -le "$total_req" ]
    then
        echo "Please make sure /tmp has around 512MB of free space to download and"
        echo "extract files from dnf_bundle."
        exit 1
    fi
else
    total_req=$(echo "(512)" | bc)
    tmp_free=$(/usr/bin/df -m /tmp | /usr/bin/sed -e /Filesystem/d | /usr/bin/awk '{print $3}')
    if [ "${tmp_free:-0}" -le "${total_req:-0}" ]; then
        echo "Please make sure /tmp has around 512MB of free space to download and"
        echo "extract files from dnf_bundle."
        exit 1
    fi
fi


# Check for specific directories related to the corrosponding OS level
if [ "$oslvl" = "7.1.0.0" ] && [ ! -e "${mnt_path}"/AIX_Toolbox_71 ]
then
    echo "No ${mnt_path}/AIX_Toolbox_71 repository path exists"
elif [ "$oslvl" = "7.2.0.0" ] && [ ! -e "${mnt_path}"/AIX_Toolbox_72 ]
then
    echo "No ${mnt_path}//AIX_Toolbox_72 repository path exists"
elif [ "$oslvl" = "7.3.0.0" ] && [ ! -e "${mnt_path}"/AIX_Toolbox_73 ]
then
    echo "No ${mnt_path}/AIX_Toolbox_73 repository path exists"
fi


# Check if /opt is having enough space to install the packages from dnf_bundle.
# Currently we need around 457MB of free space in /opt filesystem.
total_opt=$(echo "(512)" | bc)
opt_free=$(/usr/bin/df -m /opt | /usr/bin/sed -e /Filesystem/d | /usr/bin/head -1 | /usr/bin/awk '{print $3}')
if [ "${opt_free:-0}" -le "${total_opt:-0}" ]; then
    echo "Total free space required for /opt filesystem to install rpms"
    echo "  from dnf_bundle is around 512MB."
    echo "Please increase the size of /opt and retry."
    exit 1
fi

# Create a temporary directroy where the bundle is extracted.
curr_time=$(date +%Y%m%d%H%M%S)
mkdir -p /tmp/dnf-"$curr_time"
tmppath=/tmp/dnf-"$curr_time"
cd "$tmppath"

#aix_ver=`oslevel -s | awk -F- '{printf "%.1f",$1/1000}'`

if [ $aix_730_plus -eq 1 ]
then
    echo ""
    echo "Copying dnf_bundle_aix_73.tar to $tmppath ..... "
    if /usr/bin/cp "$bundle_path"/dnf_bundle_aix_73.tar "$tmppath"; then
        echo "Copy of dnf_bundle_aix_73.tar to $tmppath failed."
        exit 1
    fi
else
    echo ""
    echo "Copying dnf_bundle_aix_71_72.tar to $tmppath ....."
    
    if /usr/bin/cp "$bundle_path"/dnf_bundle_aix_71_72.tar "$tmppath"; then
        echo "Copy of dnf_bundle_aix_71_72.tar to $tmppath failed."
        exit 1
    fi
fi
#end of perl download

if [ $aix_730_plus -eq 1 ]
then
    printf "\nExtracting dnf_bundle_aix_73.tar ..."
    /usr/bin/tar -xvf dnf_bundle_aix_73.tar
else
    printf "\nExtracting dnf_bundle_aix_71_72.tar ..."
    /usr/bin/tar -xvf dnf_bundle_aix_71_72.tar
fi

./install_dnf.sh "$mnt_path" "$yum4" "$yum3_instd" 2
rc=$?
if [ $rc -eq 0 ]
then
    cd - >/dev/null 2>&1
    rm -rf "$tmppath"
elif [ $rc -ne 0 ]
then
    echo "Please check the failure error, correct it and retry again."
    cd ~
    rm -rf "$tmppath"
    exit 1
fi

# Now exit the dnf.conf file to point to local repository.

echo "Creating the dnf.conf file with required locale repositories."
echo "The default /opt/freeware/etc/dnf/dnf.conf has been saved as /opt/freeware/etc/dnf/dnf.conf_local_bak"

CONF_FILE=/opt/freeware/etc/dnf/dnf.conf
/usr/bin/mv /opt/freeware/etc/dnf/dnf.conf /opt/freeware/etc/dnf/dnf.conf_local_bak

{
echo "[main]"
echo "cachedir=/var/cache/dnf"
echo "keepcache=1"
echo "debuglevel=2"
echo "logfile=/var/log/dnf.log"
echo "exactarch=1"
echo "gpgcheck=1"
echo "installonly_limit=3"
echo "clean_requirements_on_remove=True"
echo "best=True"
echo "optional_metadata_types=filelists"
echo ""
echo "plugins=1"
echo ""
echo "[Local_AIX_Toolbox]"
echo "name=Local AIX generic repository"
echo "baseurl=file://${mnt_path}/AIX_Toolbox"
echo "enabled=1"
echo "gpgcheck=1"
echo "gpgkey=file:///opt/freeware/etc/dnf/RPM-GPG-KEY-IBM-AIX-Toolbox"
echo ""
echo "[Local_AIX_Toolbox_noarch]"
echo "name=Local AIX noarch repository"
echo "baseurl=file://${mnt_path}/AIX_Toolbox_noarch"
echo "enabled=1"
echo "gpgcheck=1"
echo "gpgkey=file:///opt/freeware/etc/dnf/RPM-GPG-KEY-IBM-AIX-Toolbox"
echo ""
} >> $CONF_FILE
if [ "$oslvl" = "7.1.0.0" ]
then
    {
    echo "[Local_AIX_Toolbox_71]"
    echo "name=Local AIX 7.1 specific repository"
    echo "baseurl=file://${mnt_path}/AIX_Toolbox_71"
    echo "enabled=1"
    echo "gpgcheck=1"
    echo "gpgkey=file:///opt/freeware/etc/dnf/RPM-GPG-KEY-IBM-AIX-Toolbox"
    echo ""
     } >> $CONF_FILE
elif [ "$oslvl" = "7.2.0.0" ]
then
    {
    echo "[Local_AIX_Toolbox_72]"
    echo "name=Local AIX 7.2 specific repository"
    echo "baseurl=file://${mnt_path}/AIX_Toolbox_72"
    echo "enabled=1"
    echo "gpgcheck=1"
    echo "gpgkey=file:///opt/freeware/etc/dnf/RPM-GPG-KEY-IBM-AIX-Toolbox"
    echo ""
     } >> $CONF_FILE
elif [ "$oslvl" = "7.3.0.0" ]
then
    {
    echo "[Local_AIX_Toolbox_73]"
    echo "name=Local AIX 7.3 specific repository"
    echo "baseurl=file://${mnt_path}/AIX_Toolbox_73"
    echo "enabled=1"
    echo "gpgcheck=1"
    echo "gpgkey=file:///opt/freeware/etc/dnf/RPM-GPG-KEY-IBM-AIX-Toolbox"
    echo ""
    } >> $CONF_FILE
else
    echo "Failed to add AIX local version specific repository."
fi