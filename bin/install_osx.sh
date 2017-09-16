#!/bin/sh

if hash brew 2>/dev/null; then
		echo "homebrew installed"
else
	echo "installing homebrew"
		ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
fi

if brew ls --versions python3 > /dev/null; then
	echo "python3 installed"
else
	echo "installing python3"
		brew install python3
fi

pip install virtualenv
virtualenv venv --python=/usr/local/bin/python3
source venv/bin/activate
pip install -r requirements.txt
