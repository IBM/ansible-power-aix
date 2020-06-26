## Sanity Testing
Before submiting your contributions we invite you to run some tests to check it will integrate correctly.
We are using TravisCI to automate some sanity tests and Ansible Galaxy has its own set of tests. Going through the following will ease the submission process.

### Setup a docker container to run as TravisCI does locally
To install Docker Engine on Ubuntu refers to: [docker docs - Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu) page.

#### New container
You can look for images on the [TravisCI Docker hub](https://hub.docker.com/u/travisci) page.<br>
Or look in the TravisCI build log, open the show more button for WORKER INFORMATION and find the INSTANCE line:
```
instance: travis-job-0f6264ed-5682-4548-864e-1786307cc2ba travis-ci-ubuntu-1804-1582576938-a9b1ae58 (via amqp)
```
We will use an image from ubuntu-1804.
You can set a couple of variables to ease future commands:
```
BUILDID="build-$RANDOM"
INSTANCE="travisci/ci-ubuntu-1804:packer-1582574251-a9b1ae5"
```
Pull the image:
```
sudo docker pull $INSTANCE
Digest: sha256:f27bad27ed683fa95fc46342f26f5bc3e03763f3ce6b7ff72351316694f2b058
Status: Downloaded newer image for travisci/ci-ubuntu-1804:packer-1582574251-a9b1ae58
docker.io/travisci/ci-ubuntu-1804:packer-1582574251-a9b1ae58
```
Initialize and run the container
```
sudo docker run --name $BUILDID -dit $INSTANCE /sbin/init
sudo docker exec -it $BUILDID bash -l
```

#### Existing container
```
CONTAINER_ID=$(sudo docker ps -q -l); sudo docker start $CONTAINER_ID && sudo docker attach $CONTAINER_ID &
BUILDID=$(sudo docker ps -l | awk '!/CONTAINER/ {print $NF}'); sudo docker exec -it $BUILDID bash -l
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

### Setup the virtual environement
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
You can use the follwoing to get to a specific commit:
```
git checkout -qf $COMMIT_HASH
```
Install and setup the virtual environement
```
add-apt-repository ppa:deadsnakes/ppa
apt-get install python3-venv
# following pip installations are required for ansible-test
pip install wheel Jinja2
pip3 install pyyaml voluptuous
pip2 install pyyaml
pip install pycodestyle pylint yamllint

git clone git://github.com/ansible/ansible.git
cd ansible
python3 -m venv venv
. venv/bin/activate
pip install --user -r requirements.txt
. hacking/env-setup
pip install --user -r docs/docsite/requirements.txt
```
For an existing virtual environement:
```
. venv/bin/activate && . hacking/env-setup
```

### Run the tests

Install some requirements:
```
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

### Documentation generation
Install some requirements:
```
pip3 install ansible-doc-extractor
```
```
DOC_SRC_DIR=~/build/IBM/ansible-power-aix/docs/source
DOC_BLD_DIR=~/build/IBM/ansible-power-aix/docs/build
cd ~/build/IBM/ansible-power-aix
```

Extract the document from modules:
```
ansible-doc-extractor --template templates/module.rst.j2 $DOC_SRC_DIR/modules $MODULE_DIR/*.py
```

Render the documentation with Sphinx:
```
pip install sphinx
pip install sphinx_rtd_theme
sphinx-build -b html $DOC_SRC_DIR $DOC_BLD_DIR
```
