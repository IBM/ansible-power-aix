# TESTS=`ls -r -l integration_migration*  | awk ' { print $9 }' | grep -v test01`
TESTS=`ls -r -l integration_migration*  | awk ' { print $9 }'`

echo "Running Ansible AIX Migration tests"
echo $TESTS
echo "enter to continue"
read nada

for test in $TESTS; do
   echo "ansible-playbook -i inventory -e target_system=nim-server $test  -v"
   ansible-playbook -i inventory -e 'target_system=nim-server' $test  -v
done
