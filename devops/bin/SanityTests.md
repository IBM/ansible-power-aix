## Sanity Testing
Before submiting your contributions we invite you to run some tests to check it will integrate correctly.
We are using TravisCI to automate some sanity tests and Ansible Galaxy has its own set of tests. Going through the following will ease the submission process.

### Setup a docker container to run TravisCI locally
To install Docker Engine on Ubuntu refers to: [docker docs - Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu) page.

#### New container
You can look for images on the [TravisCI Docker hub](https://hub.docker.com/u/travisci) page.<br>
Or look in the TravisCI build log, open the show more button for WORKER INFORMATION and find the INSTANCE line:
```
instance: travis-job-0f6264ed-5682-4548-864e-1786307cc2ba travis-ci-ubuntu-1804-1582576938-a9b1ae58 (via amqp)
```
We will use an image from ubuntu-1804.
Pull the image, start
```
CONTAINER_NAME=travis-debug
INSTANCE=travisci/ci-ubuntu-1804:packer-minimal-1593521626-ca42795e
sudo docker pull $INSTANCE
sudo docker run --name $CONTAINER_NAME -dit $INSTANCE /sbin/init
sudo docker exec -it $CONTAINER_NAME bash -l
```

#### Existing container
```
CONTAINER_ID=$(sudo docker ps -q -l); sudo docker start $CONTAINER_ID
CONTAINER_NAME=$(sudo docker ps -l | awk '!/travis/ {print $NF}'); sudo docker exec -it $CONTAINER_NAME bash -l
```

#### Cleanup
Here are some useful command to help cleanup the docker objects
Containers:
```
CONTAINER_ID=$(sudo docker ps -a -q)
sudo docker stop $CONTAINER_ID
sudo docker rm $CONTAINER_ID
```
Images:
```
sudo docker images -a
sudo docker rmi $IMAGE_ID
```

### Run your Travis file as a script
Run the following instrustions replacing REPO=IBM/ansible-power-aix by your own repository: REPO=AUTHOR/PROJECT to build the travis script:
```
su - travis
cd ~/builds
export REPO=IBM/ansible-power-aix
git clone https://github.com/travis-ci/travis-build
cd travis-build/
mkdir ~/.travis
ln -s $PWD ~/.travis/travis-build
bundle update --bundler
bundle install --gemfile ~/.travis/travis-build/Gemfile
bundler binstubs travis
cd ~/builds
# get the travis file from Git
git clone --depth=50 --branch=dev-collection git://github.com/$REPO.git IBM/ansible-power-aix
cd $REPO
# Remove the token and deploy lines before compiling the file
sed -i -e '/^env/,+3d' -e '/^deploy/,$d' .travis.yml
~/.travis/travis-build/bin/travis compile > travisci.sh
# set the branch in the travisci.sh file
sed -i 's,--branch\\=\\\x27\\\x27,--branch\\=dev-collection,g' travisci.sh
bash travisci.sh
```
Note that the Travis build is run against files from /home/travis/build/$REPO NOT from /home/travis/builds/$REPO.
<br>
Before running the travis build again, you should do some cleanup:
```
rm -rf ~/ansible
rm -rf ~/build/IBM
```

#### Run specific test
You can modify locally the module file to check changes or get a modified file from your system using:
```
docker cp ~/ansible-power-aix/plugins/modules/emgr.py travis-debug:/home/travis/builds/IBM/ansible-power-aix/plugins/modules/
```
Then in the container, fix ownership and rights:
```
sudo chown travis:travis ~/builds/IBM/ansible-power-aix/plugins/modules/emgr.py
chmod 664 ~/builds/IBM/ansible-power-aix/plugins/modules/emgr.py
```

You cannot run the travisci.sh script because it will checkout the code directly from the repository in /home/travis/build. <br>
Instead you can run:
```
cd ~/ansible
. venv/bin/activate
. hacking/env-setup
cp ~/builds/IBM/ansible-power-aix/plugins/modules/*.py ~/ansible/lib/ansible/modules/
ansible-test sanity emgr --python=3.7
```
You can run a specific sanity test with:
```
ansible-test sanity --test validate-modules emgr --python=3.7
ansible-test sanity --test validate-modules --python=3.7
```

### Run the Travis steps manually
Instead of using the travis file to run automatically the script, you can run instructions step by step.
The following instructions are based on the current version of .travis.yml and devops/bin files and might need adjustments.

#### Setup the virtual environement manually
Run as Travis:
```
su - travis
mkdir /home/travis/build && cd /home/travis/build
```
Get your github code
```
git clone git://github.com/IBM/ansible-power-aix.git IBM/ansible-power-aix
cd IBM/ansible-power-aix
```
You can use the following to get to a specific commit:
```
git checkout -qf $COMMIT_HASH
```
Install and setup the virtual environement
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3-venv

# following pip installations are required for ansible-test
pip install wheel Jinja2

git clone git://github.com/ansible/ansible.git
cd ansible
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
. hacking/env-setup
pip install -r docs/docsite/requirements.txt
```
For an existing virtual environement:
```
. venv/bin/activate && . hacking/env-setup
```

#### Run the tests

Install some requirements:
```
pip install pylint yamllint pyyaml
pip3 install pyyaml voluptuous pycodestyle ansible-doc-extractor
[[ -e $(find ~/ansible/test/ -name sanity.txt) ]] && pip install --user -r $(find ~/ansible/test/ -name sanity.txt)
```

Put your modules at the right place:
```
cp ~/build/IBM/ansible-power-aix/plugins/modules/*.py ~/ansible/lib/ansible/modules/
```
Run your tests:
```
ansible-test sanity --test validate-modules
ansible-test sanity --test validate-modules flrtvc --python=3.7
ansible-test sanity flrtvc --python=3.7
```

#### Documentation generation
Extract the document from modules:
```
pip3 install ansible-doc-extractor
DOC_SRC_DIR=~/build/IBM/ansible-power-aix/docs/source
DOC_BLD_DIR=~/build/IBM/ansible-power-aix/docs/build
cd ~/build/IBM/ansible-power-aix
ansible-doc-extractor --template templates/module.rst.j2 $DOC_SRC_DIR/modules $MODULE_DIR/*.py
```

Render the documentation with Sphinx:
```
pip install sphinx
pip install sphinx_rtd_theme
sphinx-build -b html $DOC_SRC_DIR $DOC_BLD_DIR
```
