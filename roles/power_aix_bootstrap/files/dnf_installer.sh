#!/bin/ksh
# This scripts downloads the rpm.rte & dnf_bundle.tar
# rpm.rte-4.13.0.x which is a prequisite for dnf.
# dnf_bundle.tar contains dnf and its dependent packages.
# This script checks if any of the package from dnf_bundle is
# already installed and then installs the packages accordingly.

tmppath=${2:-$(pwd)}
arg=$1

if [[ -e /usr/opt/rpm/bin/rpm ]]
then
    RPM_CMD="/usr/opt/rpm/bin/rpm"
else
    RPM_CMD="/usr/bin/rpm"
fi

# Check if we are running this as the root user.
if [[ "$(id -u)" != "0" ]]
then
    echo "This script must be run as root."
    exit 1
fi

# First check the AIX version.
oslvl=`/usr/bin/oslevel`
aix_ver=$(/usr/bin/lslpp -qLc bos.rte | /usr/bin/awk -F':' '{print $3}')
af1=$(echo $aix_ver | /usr/bin/cut -d"." -f1)
af2=$(echo $aix_ver | /usr/bin/cut -d"." -f2)
af3=$(echo $aix_ver | /usr/bin/cut -d"." -f3)
if [[ "$oslvl" = "7.1.0.0" ]]
then
    if [[ ( ! $af1 -ge 7 ) || ( ! $af2 -ge 1 ) || ( ! $af3 -ge 3 ) ]]
    then
        echo "dnf and dependencies can be installed on AIX 7.1.3 and higher versions."
        exit 1
    fi
else
    if [[ ( ! $af1 -ge 7 ) || ( ! $af2 -ge 1 ) ]]
    then
         echo "dnf and dependencies can be installed on AIX 7.1.3 and higher versions."
         exit 1
     fi
fi

# Check if yum3 is installed.
yum3_instd=0
$RPM_CMD -qa | grep yum-3.4.3 > /dev/null 2>&1
if [[ $? -eq 0 ]]
then
    yum3_instd=1
fi

prog=${0##*/}
yum4=0

arg=`echo $1 | /usr/bin/cut -c1-3`
if [[ "$arg" = "-d" ]]
then
    yum4=1 # Install only dnf if no YUM is installed.
    if [[ $yum3_instd -eq 1 ]]
    then
        echo "YUM is already installed in the machine."
        echo "Please use the option -y to update to YUM4(dnf)."
        exit 1
    fi
elif [[ "$arg" = "-y" ]]
then
    yum4=2 # Update existing YUM3 to YUM4.
elif [[ "$arg" = "-n" ]]
then
    yum4=3 # Have both YUM and dnf at the same time.
else
    usage
fi


# Check openssl version.
function print_openssl_err {
    echo "Please install openssl 1.0.2.2001 and higher version."
    echo "You can download and install latest openssl from AIX web download site"
    echo "https://www-01.ibm.com/marketing/iwm/platform/mrs/assets?source=aixbp"
    exit 1
}
ssl_ver=$(lslpp -Lc openssl.base | /usr/bin/awk 'FNR==2' | /usr/bin/awk -F':' '{print $3}')
f1=$(echo "$ssl_ver" | /usr/bin/cut -d"." -f1)
f2=$(echo "$ssl_ver" | /usr/bin/cut -d"." -f2)
f3=$(echo "$ssl_ver" | /usr/bin/cut -d"." -f3)
f4=$(echo "$ssl_ver" | /usr/bin/cut -d"." -f4)
if [[ ( ! $f1 -ge 1 ) || ( ! $f2 -ge 0 ) || ( ! $f3 -ge 0) ]]
then
     print_openssl_err
elif [[ ( $f2 -eq 0 ) && (  $f3 -eq 1) ]]
then
    print_openssl_err
else
    if [[ ( $f1 -eq 1 ) && ($f2 -eq 0 ) && ( $f3 -eq 2 ) ]]
    then
        if [[ ( ! $f4 -ge 2001 ) ]]
        then
             print_openssl_err
        fi
    fi
fi

oslvl=$(/usr/bin/oslevel)
aix_730_plus=0
os_f1=$(echo "$oslvl" | /usr/bin/cut -d"." -f1)
os_f2=$(echo "$oslvl" | /usr/bin/cut -d"." -f2)
os_f3=$(echo "$oslvl" | /usr/bin/cut -d"." -f3)
os_f4=$(echo "$oslvl" | /usr/bin/cut -d"." -f4)
if [[ ( $os_f1 -ge 7 ) && ( $os_f2 -ge 3 ) && ( $os_f3 -ge 0 ) && ( $os_f4 -ge 0 ) ]]
then
    aix_730_plus=1
fi 

aix_715_prior=0
oslvl_tl=`/usr/bin/lslpp -qLc bos.rte | /usr/bin/cut -d: -f3`
os_f1=$(echo $oslvl_tl | /usr/bin/cut -d"." -f1)
os_f2=$(echo $oslvl_tl | /usr/bin/cut -d"." -f2)
os_f3=$(echo $oslvl_tl | /usr/bin/cut -d"." -f3)
if [[ ( $os_f1 -eq 7 ) && ( $os_f2 -eq 1 ) && ( $os_f3 -lt 5 ) ]]
then
    aix_715_prior=1
fi

# Check if /tmp has enough space to download rpm.rte & dnf_bundle
# and size for extracting rpm packages.
# For 71_72 bundle it requires around 340 MB of free space.
# 170M for bundle which includes rpm.rte (40M) and rpm packages (130M).
# rpm packages extracted.
if [[ $aix_730_plus -eq 1 ]]
then
    typeset -i total_req=$(echo "(270)" | bc)
    tmp_free=$(/usr/bin/df -m "$tmppath" | sed -e /Filesystem/d | awk '{print $3}' | bc)
    if [[ $tmp_free -le $total_req ]]
    then
      chfs -a size=+$(( total_req - tmp_free ))M "$tmppath"
      if [[ $? -ne 0 ]];
      then
          echo "Please make sure $tmppath has around 270MB of free space to download and"
          echo "extract files from dnf_bundle."
          exit 1
      fi
    fi
else
    typeset -i total_req=`echo "(340)" | bc`
    tmp_free=`/usr/bin/df -m "$tmppath" | sed -e /Filesystem/d | awk '{print $3}'`
    if [[ $tmp_free -le $total_req ]]
    then
      chfs -a size=+$(( total_req - tmp_free ))M "$tmppath"
      if [[ $? -ne 0 ]];
      then
        echo "Please make sure $tmppath has around 340MB of free space to download and"
        echo "extract files from dnf_bundle."
        exit 1
      fi
    fi
fi

# Check if /opt is having enough space to install the packages from dnf_bundle.
# Currently we need around 457MB of free space in /opt filesystem.
typeset -i total_opt=`echo "(512)" | bc`
opt_free=`/usr/bin/df -m /opt | sed -e /Filesystem/d | head -1 | awk '{print $3}'`
if [[ $opt_free -le $total_opt ]]
then
    chfs -a size=+$(( total_opt - opt_free ))M /opt
    if [[ $? -ne 0 ]];
    then
      echo "Total free space required for /opt filesystem to install rpms"
      echo "  from dnf_bundle is around 512MB."
      echo "Please increase the size of /opt and retry."
      exit 1
    fi
fi

# Create a temporary directroy where all downloads should go.
curr_time=`date +%Y%m%d%H%M%S`
mkdir -p /tmp/dnf-$curr_time
tmppath=`echo /tmp/dnf-$curr_time`
cd $tmppath



if [[ $aix_715_prior -eq 1 ]]
then
    echo "Attempting download of dnf_bundle_aix_71_72.tar ..."
    username="anonymous"
    userpassword="anonymous"

    /usr/bin/expect <<DNFEOF
        log_user 0
        set timeout -1
        spawn ftp -s public.dhe.ibm.com
        expect "Name (public.dhe.ibm.com:*): "
        send "$username\r"
        expect "Password:"
        send "$userpassword\r"
        expect "ftp>"
        send "lcd $tmppath\r"
        expect "ftp>"
        send "bin\r"
        expect "ftp>"
        send "passive\r"
        expect "ftp>"
        send "cd aix/freeSoftware/aixtoolbox/ezinstall/ppc\r"
        expect "ftp>"
        send "get dnf_bundle_aix_71_72.tar\r"
        expect "ftp>"
        send "bye\r"
        expect eof
DNFEOF
   if [[ ! -e  dnf_bundle_aix_71_72.tar ]]
   then
       echo "Failed to download dnf_bundle_aix_71_72.tar."
       cd - >/dev/null 2>&1
       rm -rf $tmppath
       exit 1
   fi   
elif [[ $aix_730_plus -eq 1 ]]
then
    echo "Attempting download of dnf_bundle_aix_73.tar ..."
    export PERL_LWP_SSL_VERIFY_HOSTNAME=0
    LDR_CNTRL=MAXDATA=0x80000000@DSA /usr/opt/perl5/bin/lwp-download https://public.dhe.ibm.com/aix/freeSoftware/aixtoolbox/ezinstall/ppc/dnf_bundle_aix_73.tar
    if [[ $? -ne 0 ]]
    then
        echo "Failed to download dnf_bundle_aix_73.tar"
        cd - >/dev/null 2>&1
        rm -rf $tmppath
        exit 1
    fi

    # Do this once rpm.rte for 730 is available on AIX Toolbox.
    #/usr/opt/perl5/bin/lwp-download http://public.dhe.ibm.com/aix/freeSoftware/aixtoolbox/INSTALLP/ppc/rpm.rte
    #if [[ $? -ne 0 ]]
    #then
    #    echo "Failed to download rpm.rte"
    #    exit 1
    #fi
else
    echo "Attempting download of dnf_bundle_aix_71_72.tar ..."
    LDR_CNTRL=MAXDATA=0x80000000@DSA /usr/opt/perl5/bin/lwp-download https://public.dhe.ibm.com/aix/freeSoftware/aixtoolbox/ezinstall/ppc/dnf_bundle_aix_71_72.tar
     if [[ $? -ne 0 ]]
     then
        echo "Failed to download dnf_bundle_aix_71_72.tar"
        cd - >/dev/null 2>&1
        rm -rf $tmppath
        exit 1
     fi 
    #/usr/opt/perl5/bin/lwp-download http://public.dhe.ibm.com/aix/freeSoftware/aixtoolbox/INSTALLP/ppc/rpm.rte
    # if [[ $? -ne 0 ]]
    # then
    #    echo "Failed to download  rpm.rte"
    #    exit 1
    # elif [[ -e rpm.rte.txt ]]
    # then
    #     /usr/bin/mv rpm.rte.txt rpm.rte
    # fi
fi
#end of perl download

if [[ $aix_730_plus -eq 1 ]]
then
    echo "\nExtracting dnf_bundle_aix_73.tar ..."
    tar -xvf dnf_bundle_aix_73.tar
else
    echo "\nExtracting dnf_bundle_aix_71_72.tar ..."
    tar -xvf dnf_bundle_aix_71_72.tar
fi

echo "Argument passing to the installation is:"
echo $arg
echo $yum4
echo $yum3_instd

./install_dnf.sh "$arg" $yum4 $yum3_instd 2
if [[ $? -eq 0 ]]
then
    cd - >/dev/null 2>&1
    rm -rf $tmppath
    exit 0
elif [[ $? -ne 0 ]]
then
    echo "You can try installing the downloaded dnf packages from $tmppath manually."
    exit 1
fi
