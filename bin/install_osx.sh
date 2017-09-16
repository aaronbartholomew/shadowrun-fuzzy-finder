#!/bin/sh

if brew ls --versions python3 > /dev/null; then
	echo "installed"
else
		ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
		brew install python3
fi
pip install virtualenv
virtualenv venv --python=/usr/local/bin/python3
source venv/bin/activate
pip install -r requirements.txt
