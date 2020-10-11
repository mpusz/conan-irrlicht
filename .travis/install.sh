#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == 'Darwin' ]]; then
    brew update
    brew install openssl readline
    brew outdated pyenv || brew upgrade pyenv
    brew install pyenv-virtualenv
    brew outdated cmake || brew upgrade cmake

    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi

    pyenv install 3.7.1
    pyenv virtualenv 3.7.1 conan
    pyenv rehash
    pyenv activate conan
fi

pip install -U conan_package_tools
pip install -U conan
conan user
